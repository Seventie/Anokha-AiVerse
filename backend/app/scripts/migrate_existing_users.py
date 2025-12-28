# backend/app/scripts/migrate_existing_users.py

"""
One-time migration script to sync existing SQL users to Neo4j knowledge graph.
Run this AFTER initializing static graphs with init_global_graphs.py

Usage:
    python -m app.scripts.migrate_existing_users
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config.database import SessionLocal
from app.models.database import User
from app.services.user_graph_sync import get_user_graph_sync
from tqdm import tqdm  # Optional: for progress bar
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UserMigration:
    """Handles migration of existing users from SQL to Neo4j"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.sync_service = get_user_graph_sync()
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }
    
    def get_all_users(self) -> List[User]:
        """Fetch all users from SQL database"""
        logger.info("Fetching all users from PostgreSQL...")
        users = self.db.query(User).all()
        logger.info(f"Found {len(users)} users to migrate")
        return users
    
    def check_user_exists_in_graph(self, user_id: str) -> bool:
        """Check if user already exists in Neo4j"""
        from app.services.graph_db import get_graph_db
        graph_db = get_graph_db()
        
        if not graph_db.driver:
            return False
        
        with graph_db.driver.session() as session:
            result = session.run(
                "MATCH (u:User {id: $user_id}) RETURN count(u) as count",
                user_id=user_id
            )
            record = result.single()
            return record["count"] > 0 if record else False
    
    def migrate_user(self, user: User, force: bool = False) -> bool:
        """Migrate a single user to Neo4j"""
        try:
            # Check if already exists
            if not force and self.check_user_exists_in_graph(user.id):
                logger.info(f"User {user.id} already exists in graph, skipping...")
                self.stats["skipped"] += 1
                return True
            
            # Perform sync
            logger.info(f"Migrating user: {user.id} ({user.email})...")
            results = self.sync_service.sync_complete_user(user.id, self.db)
            
            # Log results
            logger.info(f"  ✓ Synced: {results}")
            self.stats["success"] += 1
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Failed to migrate user {user.id}: {e}")
            self.stats["failed"] += 1
            self.stats["errors"].append({
                "user_id": user.id,
                "email": user.email,
                "error": str(e)
            })
            return False
    
    def migrate_all(self, force: bool = False, batch_size: int = 10) -> Dict[str, Any]:
        """Migrate all users in batches"""
        logger.info("=" * 80)
        logger.info("STARTING USER MIGRATION TO NEO4J")
        logger.info("=" * 80)
        
        start_time = time.time()
        users = self.get_all_users()
        self.stats["total"] = len(users)
        
        if self.stats["total"] == 0:
            logger.warning("No users found to migrate!")
            return self.stats
        
        # Migrate users with progress tracking
        logger.info(f"\nMigrating {self.stats['total']} users...")
        logger.info(f"Force mode: {force}")
        logger.info(f"Batch size: {batch_size}\n")
        
        for i, user in enumerate(users, 1):
            logger.info(f"[{i}/{self.stats['total']}] Processing user: {user.email}")
            self.migrate_user(user, force)
            
            # Small delay between users to avoid overwhelming Neo4j
            if i % batch_size == 0:
                logger.info(f"  Batch {i//batch_size} completed. Pausing briefly...")
                time.sleep(1)
        
        # Calculate statistics
        elapsed_time = time.time() - start_time
        self.stats["elapsed_seconds"] = round(elapsed_time, 2)
        self.stats["users_per_second"] = round(self.stats["success"] / elapsed_time, 2) if elapsed_time > 0 else 0
        
        self._print_summary()
        
        return self.stats
    
    def _print_summary(self):
        """Print migration summary"""
        logger.info("\n" + "=" * 80)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Users:       {self.stats['total']}")
        logger.info(f"✓ Successfully Migrated: {self.stats['success']}")
        logger.info(f"⊘ Skipped (exists):      {self.stats['skipped']}")
        logger.info(f"✗ Failed:                {self.stats['failed']}")
        logger.info(f"Time Elapsed:            {self.stats['elapsed_seconds']}s")
        logger.info(f"Speed:                   {self.stats['users_per_second']} users/sec")
        
        if self.stats["errors"]:
            logger.info("\n" + "-" * 80)
            logger.info("ERRORS:")
            for error in self.stats["errors"]:
                logger.error(f"  User {error['user_id']} ({error['email']}): {error['error']}")
        
        logger.info("=" * 80)
        
        # Success/failure indicator
        if self.stats["failed"] == 0:
            logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        else:
            logger.warning(f"⚠️  MIGRATION COMPLETED WITH {self.stats['failed']} FAILURES")
        
        logger.info("=" * 80)
    
    def cleanup(self):
        """Close database connection"""
        self.db.close()


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate existing users to Neo4j")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-sync even if user already exists in graph"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of users to process before pausing (default: 10)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without actually syncing"
    )
    
    args = parser.parse_args()
    
    try:
        migration = UserMigration()
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            users = migration.get_all_users()
            logger.info(f"Would migrate {len(users)} users:")
            for user in users[:10]:  # Show first 10
                logger.info(f"  - {user.email} (ID: {user.id})")
            if len(users) > 10:
                logger.info(f"  ... and {len(users) - 10} more")
            return 0
        
        # Run migration
        stats = migration.migrate_all(force=args.force, batch_size=args.batch_size)
        
        # Cleanup
        migration.cleanup()
        
        # Exit code based on success
        return 0 if stats["failed"] == 0 else 1
        
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Migration interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"\n\n❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
