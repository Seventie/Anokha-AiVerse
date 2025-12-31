// frontend/src/components/Dashboard/ColdEmailModule.tsx

import React, { useState, useEffect } from 'react';
import { 
  Mail, Plus, Send, Eye, CheckCircle, XCircle, Clock, 
  AlertCircle, Loader2, Users, TrendingUp, Edit, Trash2,
  Sparkles, ExternalLink, RefreshCw
} from 'lucide-react';
import { User } from '../../services/authService';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Campaign {
  id: string;
  name: string;
  target_role: string;
  target_companies: string[];
  status: string;
  total_recipients: number;
  emails_sent: number;
  emails_opened: number;
  emails_replied: number;
  created_at: string;
}

interface Recipient {
  id: string;
  name: string;
  email: string;
  title: string;
  company: string;
  subject: string;
  body: string;
  status: string;
  approved: boolean;
}

const ColdEmailModule: React.FC<{ user: User }> = ({ user }) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form state
  const [campaignName, setCampaignName] = useState('');
  const [targetRole, setTargetRole] = useState('Software Engineer');
  const [targetCompanies, setTargetCompanies] = useState('');
  const [recipientsList, setRecipientsList] = useState('');

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchCampaigns = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/cold-email/campaigns`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setCampaigns(data.campaigns || []);
      } else {
        setError('Failed to load campaigns');
      }
    } catch (error) {
      console.error('Failed to fetch campaigns:', error);
      setError('Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  const createCampaign = async () => {
    if (!campaignName || !targetCompanies) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Parse companies
      const companies = targetCompanies.split(',').map(c => c.trim()).filter(Boolean);
      
      // Create campaign
      const campaignResponse = await fetch(`${API_URL}/api/cold-email/campaigns`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          name: campaignName,
          target_role: targetRole,
          target_companies: companies
        })
      });

      if (!campaignResponse.ok) {
        const errorData = await campaignResponse.json();
        throw new Error(errorData.detail || 'Failed to create campaign');
      }

      const campaignData = await campaignResponse.json();
      const campaignId = campaignData.campaign.id;

      // Parse recipients
      const recipientsData = recipientsList.split('\n')
        .map(line => {
          const [name, email, title, company] = line.split(',').map(s => s.trim());
          if (name && email && company) {
            return { name, email, title: title || 'Hiring Manager', company };
          }
          return null;
        })
        .filter(Boolean);

      if (recipientsData.length > 0) {
        // Add recipients
        const addRecipientsResponse = await fetch(
          `${API_URL}/api/cold-email/campaigns/${campaignId}/recipients`,
          {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ recipients: recipientsData })
          }
        );

        if (!addRecipientsResponse.ok) {
          throw new Error('Failed to add recipients');
        }

        // Generate emails
        const generateResponse = await fetch(
          `${API_URL}/api/cold-email/campaigns/${campaignId}/generate`,
          {
            method: 'POST',
            headers: getAuthHeaders()
          }
        );

        if (!generateResponse.ok) {
          throw new Error('Failed to generate emails');
        }

        // Request approval
        const approvalResponse = await fetch(
          `${API_URL}/api/cold-email/campaigns/${campaignId}/request-approval`,
          {
            method: 'POST',
            headers: getAuthHeaders()
          }
        );

        if (!approvalResponse.ok) {
          throw new Error('Failed to request approval');
        }
      }

      setSuccess('✅ Campaign created! Check your Gmail for approval request.');
      setShowCreateModal(false);
      fetchCampaigns();
      
      // Reset form
      setCampaignName('');
      setTargetCompanies('');
      setRecipientsList('');

    } catch (error: any) {
      console.error('Campaign creation error:', error);
      setError(error.message || 'Failed to create campaign');
    } finally {
      setLoading(false);
    }
  };

  const fetchRecipients = async (campaignId: string) => {
    try {
      const response = await fetch(
        `${API_URL}/api/cold-email/campaigns/${campaignId}/recipients`,
        { headers: getAuthHeaders() }
      );

      if (response.ok) {
        const data = await response.json();
        setRecipients(data.recipients || []);
      }
    } catch (error) {
      console.error('Failed to fetch recipients:', error);
    }
  };

  const approveRecipient = async (recipientId: string) => {
    try {
      const response = await fetch(
        `${API_URL}/api/cold-email/recipients/${recipientId}/approve`,
        {
          method: 'POST',
          headers: getAuthHeaders()
        }
      );

      if (response.ok) {
        setSuccess('Email approved!');
        if (selectedCampaign) fetchRecipients(selectedCampaign.id);
      } else {
        setError('Failed to approve email');
      }
    } catch (error) {
      setError('Failed to approve email');
    }
  };

  const sendApprovedEmails = async (campaignId: string) => {
    if (!confirm('Send all approved emails now?')) return;

    setLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/api/cold-email/campaigns/${campaignId}/send`,
        {
          method: 'POST',
          headers: getAuthHeaders()
        }
      );

      if (response.ok) {
        const data = await response.json();
        setSuccess(`✅ Sent ${data.sent_count} emails!`);
        fetchCampaigns();
        if (selectedCampaign) fetchRecipients(selectedCampaign.id);
      } else {
        setError('Failed to send emails');
      }
    } catch (error) {
      setError('Failed to send emails');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sent': return 'text-green-400 bg-green-500/20 border-green-500/30';
      case 'approved': return 'text-blue-400 bg-blue-500/20 border-blue-500/30';
      case 'pending': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30';
      case 'pending_approval': return 'text-purple-400 bg-purple-500/20 border-purple-500/30';
      case 'active': return 'text-green-400 bg-green-500/20 border-green-500/30';
      case 'draft': return 'text-gray-400 bg-gray-500/20 border-gray-500/30';
      default: return 'text-white/40 bg-white/5 border-white/10';
    }
  };

  if (loading && campaigns.length === 0) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-light mb-2">Cold Email Campaigns</h2>
          <p className="text-white/60">AI-powered outreach to hiring managers</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-6 py-3 bg-primary/20 hover:bg-primary/30 text-primary rounded-2xl 
                   font-bold flex items-center gap-3 transition-all border border-primary/30"
        >
          <Plus size={20} />
          New Campaign
        </button>
      </div>

      {/* Messages */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-[2rem] p-4 flex items-center gap-3">
          <AlertCircle className="text-red-400" />
          <p className="text-red-400 flex-1">{error}</p>
          <button onClick={() => setError(null)} className="text-red-400">✕</button>
        </div>
      )}

      {success && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-[2rem] p-4 flex items-center gap-3">
          <CheckCircle className="text-green-400" />
          <p className="text-green-400 flex-1">{success}</p>
          <button onClick={() => setSuccess(null)} className="text-green-400">✕</button>
        </div>
      )}

      {/* Campaigns Grid */}
      {!selectedCampaign ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {campaigns.map(campaign => (
            <div
              key={campaign.id}
              onClick={() => {
                setSelectedCampaign(campaign);
                fetchRecipients(campaign.id);
              }}
              className="bg-white/5 border border-white/10 rounded-[2rem] p-6 hover:bg-white/10 
                       transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center">
                  <Mail className="text-primary" size={24} />
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(campaign.status)}`}>
                  {campaign.status.replace('_', ' ')}
                </span>
              </div>

              <h3 className="text-lg font-medium mb-2 group-hover:text-primary transition-colors">
                {campaign.name}
              </h3>
              <p className="text-sm text-white/60 mb-4">
                {campaign.target_role} • {campaign.target_companies?.length || 0} companies
              </p>

              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="bg-white/5 rounded-xl p-3">
                  <p className="text-2xl font-light">{campaign.total_recipients}</p>
                  <p className="text-xs text-white/40">Recipients</p>
                </div>
                <div className="bg-white/5 rounded-xl p-3">
                  <p className="text-2xl font-light text-green-400">{campaign.emails_sent}</p>
                  <p className="text-xs text-white/40">Sent</p>
                </div>
                <div className="bg-white/5 rounded-xl p-3">
                  <p className="text-2xl font-light text-blue-400">{campaign.emails_replied}</p>
                  <p className="text-xs text-white/40">Replied</p>
                </div>
              </div>
            </div>
          ))}

          {campaigns.length === 0 && (
            <div className="col-span-full text-center py-12">
              <Mail size={48} className="mx-auto text-white/20 mb-4" />
              <h3 className="text-xl font-light mb-2">No campaigns yet</h3>
              <p className="text-white/40 mb-6">Create your first cold email campaign</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-6 py-3 bg-primary/20 text-primary rounded-2xl font-bold"
              >
                Get Started
              </button>
            </div>
          )}
        </div>
      ) : (
        // Campaign Details View
        <div className="space-y-6">
          <button
            onClick={() => setSelectedCampaign(null)}
            className="text-white/60 hover:text-white flex items-center gap-2"
          >
            ← Back to Campaigns
          </button>

          {/* Campaign Header */}
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-2xl font-light mb-1">{selectedCampaign.name}</h3>
                <p className="text-white/60">{selectedCampaign.target_role}</p>
              </div>
              <button
                onClick={() => sendApprovedEmails(selectedCampaign.id)}
                disabled={loading}
                className="px-6 py-3 bg-green-500/20 hover:bg-green-500/30 text-green-400 
                         rounded-2xl font-bold flex items-center gap-3 transition-all 
                         border border-green-500/30 disabled:opacity-50"
              >
                {loading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
                Send Approved
              </button>
            </div>

            <div className="grid grid-cols-4 gap-4">
              <StatCard label="Total" value={selectedCampaign.total_recipients} />
              <StatCard label="Sent" value={selectedCampaign.emails_sent} color="green" />
              <StatCard label="Opened" value={selectedCampaign.emails_opened} color="blue" />
              <StatCard label="Replied" value={selectedCampaign.emails_replied} color="purple" />
            </div>
          </div>

          {/* Recipients List */}
          <div className="space-y-4">
            {recipients.map(recipient => (
              <RecipientCard
                key={recipient.id}
                recipient={recipient}
                onApprove={approveRecipient}
              />
            ))}

            {recipients.length === 0 && (
              <div className="text-center py-12 bg-white/5 rounded-[2rem]">
                <Users size={48} className="mx-auto text-white/20 mb-4" />
                <p className="text-white/60">No recipients yet</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create Campaign Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a2f2a] border border-white/10 rounded-[2rem] p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-light">Create Cold Email Campaign</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-white/40 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              {/* Campaign Name */}
              <div>
                <label className="block text-sm font-medium mb-2">Campaign Name *</label>
                <input
                  type="text"
                  value={campaignName}
                  onChange={(e) => setCampaignName(e.target.value)}
                  placeholder="e.g., SWE Outreach - January 2025"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white 
                           placeholder-white/40 focus:outline-none focus:border-primary/50"
                />
              </div>

              {/* Target Role */}
              <div>
                <label className="block text-sm font-medium mb-2">Target Role</label>
                <input
                  type="text"
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  placeholder="Software Engineer"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white 
                           placeholder-white/40 focus:outline-none focus:border-primary/50"
                />
              </div>

              {/* Target Companies */}
              <div>
                <label className="block text-sm font-medium mb-2">Target Companies *</label>
                <input
                  type="text"
                  value={targetCompanies}
                  onChange={(e) => setTargetCompanies(e.target.value)}
                  placeholder="Google, Microsoft, Amazon (comma-separated)"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white 
                           placeholder-white/40 focus:outline-none focus:border-primary/50"
                />
              </div>

              {/* Recipients */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Recipients (one per line: Name, Email, Title, Company)
                </label>
                <textarea
                  value={recipientsList}
                  onChange={(e) => setRecipientsList(e.target.value)}
                  placeholder="John Doe, john@google.com, Engineering Manager, Google&#10;Jane Smith, jane@microsoft.com, Tech Lead, Microsoft"
                  rows={6}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white 
                           placeholder-white/40 font-mono text-sm focus:outline-none focus:border-primary/50"
                />
                <p className="text-xs text-white/40 mt-2">
                  💡 Format: Name, Email, Title, Company (one per line)
                </p>
              </div>

              {/* Actions */}
              <div className="flex gap-4">
                <button
                  onClick={createCampaign}
                  disabled={loading}
                  className="flex-1 px-6 py-3 bg-primary/20 hover:bg-primary/30 text-primary 
                           rounded-2xl font-bold flex items-center justify-center gap-3 transition-all 
                           border border-primary/30 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader2 className="animate-spin" size={20} />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Sparkles size={20} />
                      Create & Generate Emails
                    </>
                  )}
                </button>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-6 py-3 bg-white/5 hover:bg-white/10 text-white rounded-2xl font-bold"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper Components
const StatCard: React.FC<{ label: string; value: number; color?: string }> = ({ 
  label, value, color = 'white' 
}) => (
  <div className="bg-white/5 rounded-xl p-4 text-center">
    <p className={`text-3xl font-light ${color === 'white' ? 'text-white' : `text-${color}-400`}`}>
      {value}
    </p>
    <p className="text-xs text-white/40 mt-1">{label}</p>
  </div>
);

const RecipientCard: React.FC<{
  recipient: Recipient;
  onApprove: (id: string) => void;
}> = ({ recipient, onApprove }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h4 className="font-medium text-lg">{recipient.name}</h4>
          <p className="text-sm text-white/60">{recipient.title} at {recipient.company}</p>
          <p className="text-xs text-white/40 mt-1">{recipient.email}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 rounded-full text-xs font-medium border 
            ${recipient.status === 'sent' ? 'text-green-400 bg-green-500/20 border-green-500/30' :
              recipient.status === 'approved' ? 'text-blue-400 bg-blue-500/20 border-blue-500/30' :
              'text-yellow-400 bg-yellow-500/20 border-yellow-500/30'}`}>
            {recipient.status}
          </span>
          {!recipient.approved && recipient.status === 'pending' && (
            <button
              onClick={() => onApprove(recipient.id)}
              className="px-4 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 
                       rounded-xl font-medium text-sm border border-green-500/30"
            >
              <CheckCircle size={16} className="inline mr-2" />
              Approve
            </button>
          )}
        </div>
      </div>

      <div className="border-t border-white/10 pt-4">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-sm text-primary hover:underline flex items-center gap-2"
        >
          <Eye size={16} />
          {expanded ? 'Hide' : 'Preview'} Email
        </button>

        {expanded && (
          <div className="mt-4 space-y-3">
            <div className="bg-white/5 rounded-xl p-4">
              <p className="text-xs text-white/40 mb-1">Subject:</p>
              <p className="font-medium">{recipient.subject || 'No subject'}</p>
            </div>
            <div className="bg-white/5 rounded-xl p-4">
              <p className="text-xs text-white/40 mb-2">Body:</p>
              <div className="text-sm text-white/80 leading-relaxed whitespace-pre-wrap">
                {recipient.body || 'No email body generated'}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ✅ DEFAULT EXPORT
export default ColdEmailModule;
