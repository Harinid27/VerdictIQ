import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  User,
  Shield,
  Building,
  Mail,
  Phone,
  FileText,
  Scale,
  Calendar,
  CheckCircle,
  XCircle,
  Clock,
  Briefcase,
  Edit,
  Upload,
  AlertCircle,
  TrendingUp,
  FolderOpen,
  FileCheck,
  Zap,
  X,
  Save,
  Trash2,
  Image as ImageIcon,
} from 'lucide-react';

interface ProfilePageProps {
  userEmail: string;
  userName: string;
  organizationName: string;
  userRole: string;
}

interface ActivityStats {
  casesCreated: number;
  casesAnalyzed: number;
  reportsGenerated: number;
  evidenceUploaded: number;
  aiAnalysesPerformed: number;
}

export const ProfilePage: React.FC<ProfilePageProps> = ({
  userEmail,
  userName,
  organizationName,
  userRole,
}) => {
  // Modal states
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isPhotoModalOpen, setIsPhotoModalOpen] = useState(false);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [editFormData, setEditFormData] = useState({
    phone: '',
    specialization: '',
    barNumber: '',
    jurisdiction: '',
    yearsOfExperience: '',
    bio: '',
  });

  // Extended profile fields (would come from backend in production)
  const [profileData, setProfileData] = useState({
    phone: '',
    specialization: '',
    barNumber: '',
    jurisdiction: '',
    yearsOfExperience: '',
    bio: '',
    profilePhoto: null as string | null,
  });

  const [activityStats, setActivityStats] = useState<ActivityStats>({
    casesCreated: 0,
    casesAnalyzed: 0,
    reportsGenerated: 0,
    evidenceUploaded: 0,
    aiAnalysesPerformed: 0,
  });

  const [verificationStatus, setVerificationStatus] = useState({
    emailVerified: true, // User is logged in, so email is verified
    identityVerified: false,
    professionalVerified: false,
    profileCompletion: 0,
  });

  const [recentActivity] = useState([
    { type: 'case', title: 'Smith vs. Johnson', time: '2 hours ago' },
    { type: 'report', title: 'Evidentiary Analysis Report', time: '1 day ago' },
    { type: 'login', title: 'Last login', time: '2 days ago' },
  ]);

  // Load profile data from localStorage on mount (user-specific)
  useEffect(() => {
    if (!userEmail) {
      // Clear profile data when no user is logged in
      setProfileData({
        phone: '',
        specialization: '',
        barNumber: '',
        jurisdiction: '',
        yearsOfExperience: '',
        bio: '',
        profilePhoto: null,
      });
      setEditFormData({
        phone: '',
        specialization: '',
        barNumber: '',
        jurisdiction: '',
        yearsOfExperience: '',
        bio: '',
      });
      return;
    }

    const userSpecificPhotoKey = `verdictiq_profile_photo_${userEmail}`;
    const userSpecificDataKey = `verdictiq_profile_data_${userEmail}`;

    const savedPhoto = localStorage.getItem(userSpecificPhotoKey);
    const savedData = localStorage.getItem(userSpecificDataKey);

    if (savedData) {
      try {
        const parsedData = JSON.parse(savedData);
        setProfileData({
          phone: parsedData.phone || '',
          specialization: parsedData.specialization || '',
          barNumber: parsedData.barNumber || '',
          jurisdiction: parsedData.jurisdiction || '',
          yearsOfExperience: parsedData.yearsOfExperience || '',
          bio: parsedData.bio || '',
          profilePhoto: savedPhoto || null,
        });
        setEditFormData({
          phone: parsedData.phone || '',
          specialization: parsedData.specialization || '',
          barNumber: parsedData.barNumber || '',
          jurisdiction: parsedData.jurisdiction || '',
          yearsOfExperience: parsedData.yearsOfExperience || '',
          bio: parsedData.bio || '',
        });
      } catch (error) {
        console.error('Error loading profile data:', error);
        // If data is corrupted, load just the photo
        setProfileData({
          phone: '',
          specialization: '',
          barNumber: '',
          jurisdiction: '',
          yearsOfExperience: '',
          bio: '',
          profilePhoto: savedPhoto || null,
        });
      }
    } else {
      // Load only photo if no profile data exists
      setProfileData({
        phone: '',
        specialization: '',
        barNumber: '',
        jurisdiction: '',
        yearsOfExperience: '',
        bio: '',
        profilePhoto: savedPhoto || null,
      });
    }
  }, [userEmail]); // Reload when userEmail changes

  // Fetch activity statistics from backend
  useEffect(() => {
    const fetchActivityStats = async () => {
      const token = localStorage.getItem('verdictiq_token');
      if (!token) return;

      try {
        // Fetch cases count
        const casesRes = await fetch('http://localhost:8000/api/cases/all', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const casesData = await casesRes.json();

        // Fetch reports count
        const reportsRes = await fetch('http://localhost:8000/api/agent3/reports/all', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const reportsData = await reportsRes.json();

        setActivityStats({
          casesCreated: casesData.success ? casesData.data?.length || 0 : 0,
          casesAnalyzed: casesData.success ? casesData.data?.length || 0 : 0,
          reportsGenerated: reportsData.success ? reportsData.data?.length || 0 : 0,
          evidenceUploaded: 0, // Would need separate endpoint
          aiAnalysesPerformed: reportsData.success ? reportsData.data?.length || 0 : 0,
        });
      } catch (error) {
        console.error('Error fetching activity stats:', error);
      }
    };

    fetchActivityStats();
  }, [userEmail]); // Re-fetch when user changes

  // Get user initials for avatar
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };



  // Calculate profile completion dynamically
  const calculateProfileCompletion = () => {
    const fields = [
      userName, // Name
      userEmail, // Email
      userRole, // Role
      organizationName, // Organization
      profileData.profilePhoto, // Profile Photo
      profileData.phone, // Phone
      profileData.bio, // Bio
      profileData.yearsOfExperience, // Experience
      profileData.specialization, // Specialization
    ];

    const completedFields = fields.filter(field => field && field !== '' && field !== null).length;
    return Math.round((completedFields / fields.length) * 100);
  };

  // Open edit profile modal
  const handleOpenEditModal = () => {
    setEditFormData({
      phone: profileData.phone,
      specialization: profileData.specialization,
      barNumber: profileData.barNumber,
      jurisdiction: profileData.jurisdiction,
      yearsOfExperience: profileData.yearsOfExperience,
      bio: profileData.bio,
    });
    setIsEditModalOpen(true);
  };

  // Save profile data
  const handleSaveProfile = () => {
    // Update profile data state
    setProfileData(prev => ({ ...prev, ...editFormData }));

    // Save to localStorage (user-specific)
    const userSpecificDataKey = `verdictiq_profile_data_${userEmail}`;
    localStorage.setItem(userSpecificDataKey, JSON.stringify(editFormData));

    setIsEditModalOpen(false);
  };

  // Open photo management modal
  const handleOpenPhotoModal = () => {
    setPhotoPreview(profileData.profilePhoto);
    setIsPhotoModalOpen(true);
  };

  // Handle photo selection in modal
  const handlePhotoSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      alert('Please upload a valid image file (JPG, JPEG, PNG, or WEBP)');
      return;
    }

    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
      alert('File size must be less than 5MB');
      return;
    }

    const reader = new FileReader();
    reader.onloadend = () => {
      setPhotoPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  // Save photo from modal
  const handleSavePhoto = () => {
    if (photoPreview) {
      const userSpecificKey = `verdictiq_profile_photo_${userEmail}`;
      setProfileData(prev => ({ ...prev, profilePhoto: photoPreview }));
      localStorage.setItem(userSpecificKey, photoPreview);
      // Dispatch event to notify Navbar of photo change
      window.dispatchEvent(new CustomEvent('profilePhotoUpdated', { detail: { userEmail } }));
    }
    setIsPhotoModalOpen(false);
    setPhotoPreview(null);
  };

  // Remove photo
  const handleRemovePhoto = () => {
    const userSpecificKey = `verdictiq_profile_photo_${userEmail}`;
    setProfileData(prev => ({ ...prev, profilePhoto: null }));
    localStorage.removeItem(userSpecificKey);
    // Dispatch event to notify Navbar of photo removal
    window.dispatchEvent(new CustomEvent('profilePhotoUpdated', { detail: { userEmail } }));
    setIsPhotoModalOpen(false);
    setPhotoPreview(null);
  };

  // Update profile completion when profile data changes
  useEffect(() => {
    const completion = calculateProfileCompletion();
    setVerificationStatus(prev => ({ ...prev, profileCompletion: completion }));
  }, [userName, userEmail, userRole, organizationName, profileData]);

  // Reset activity stats when user changes (on login/logout with different user)
  useEffect(() => {
    // Reset activity stats to fetch fresh data for current user
    setActivityStats({
      casesCreated: 0,
      casesAnalyzed: 0,
      reportsGenerated: 0,
      evidenceUploaded: 0,
      aiAnalysesPerformed: 0,
    });
  }, [userEmail]); // Trigger when userEmail changes (new user login)

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h2 className="text-xl font-bold uppercase tracking-wider text-white font-display flex items-center gap-2">
          <User className="w-5 h-5 text-brand-blue" />
          Profile
        </h2>
        <p className="text-xs text-brand-textMuted mt-0.5">
          Manage your account, professional information, verification status, and profile settings.
        </p>
      </div>

      {/* Profile Header Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="rounded-2xl bg-brand-dark/45 border border-white/5 p-6 md:p-8 shadow-premium-card relative overflow-hidden"
      >
        {/* Ambient Lighting */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-brand-blue/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-brand-purple/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row items-center md:items-start gap-6">
          {/* Profile Photo */}
          <div className="relative shrink-0">
            <div className="absolute w-28 h-28 rounded-full bg-gradient-to-br from-brand-blue/30 to-brand-purple/30 blur-xl animate-pulse" />
            {profileData.profilePhoto ? (
              <div className="w-24 h-24 rounded-full border-2 border-brand-blue/30 bg-brand-dark overflow-hidden relative z-10">
                <img src={profileData.profilePhoto} alt="Profile" className="w-full h-full object-cover" />
              </div>
            ) : (
              <div className="w-24 h-24 rounded-full border-2 border-brand-blue/30 bg-brand-dark flex items-center justify-center text-white relative z-10">
                <span className="text-2xl font-bold text-brand-blue">{getInitials(userName)}</span>
              </div>
            )}
            <button
              onClick={handleOpenPhotoModal}
              className="absolute bottom-0 right-0 p-2 rounded-full bg-brand-blue text-white border border-white/10 hover:bg-brand-blue/80 transition-all duration-300 z-20"
            >
              <Upload className="w-3 h-3" />
            </button>
          </div>

          {/* Profile Info */}
          <div className="flex-1 text-center md:text-left">
            <div className="flex flex-col md:flex-row md:items-center gap-3 justify-center md:justify-start mb-3">
              <h3 className="text-2xl font-bold font-display text-white">{userName}</h3>
              <div className="flex items-center gap-2 justify-center md:justify-start">
                <span className="px-3 py-1 rounded-full bg-brand-blue/10 border border-brand-blue/20 text-xs text-brand-blue uppercase tracking-wider font-bold capitalize">
                  {userRole}
                </span>
                {verificationStatus.emailVerified && (
                  <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                    <CheckCircle className="w-3 h-3 text-emerald-400" />
                    <span className="text-[10px] text-emerald-400 uppercase font-semibold">Verified</span>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-2 text-sm text-brand-textMuted/80">
              <div className="flex items-center justify-center md:justify-start gap-2">
                <Building className="w-4 h-4 text-brand-blue/60" />
                <span className="text-white">{organizationName}</span>
              </div>
              <div className="flex items-center justify-center md:justify-start gap-2">
                <Mail className="w-4 h-4 text-brand-blue/60" />
                <span>{userEmail}</span>
              </div>
              {profileData.phone && (
                <div className="flex items-center justify-center md:justify-start gap-2">
                  <Phone className="w-4 h-4 text-brand-blue/60" />
                  <span>{profileData.phone}</span>
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-3 mt-4 justify-center md:justify-start">
              <button
                onClick={handleOpenEditModal}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-blue/10 border border-brand-blue/20 text-brand-blue text-xs font-semibold hover:bg-brand-blue/20 transition-all duration-300"
              >
                <Edit className="w-3 h-3" />
                Edit Profile
              </button>
              <button
                onClick={handleOpenPhotoModal}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-xs font-semibold hover:bg-white/10 transition-all duration-300"
              >
                <Upload className="w-3 h-3" />
                Change Photo
              </button>
            </div>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Professional Info & Verification */}
        <div className="lg:col-span-2 space-y-6">
          {/* Verification Status Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="rounded-2xl bg-brand-dark/30 border border-white/5 p-6 shadow-premium-card"
          >
            <h3 className="text-sm font-bold uppercase tracking-wider text-white font-display flex items-center gap-2 mb-4">
              <Shield className="w-4 h-4 text-brand-blue" />
              Verification Status
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-brand-dark/40 border border-white/5">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-brand-textMuted uppercase tracking-wider">Email Verification</span>
                  {verificationStatus.emailVerified ? (
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-400" />
                  )}
                </div>
                <span className={`text-xs font-semibold ${verificationStatus.emailVerified ? 'text-emerald-400' : 'text-red-400'}`}>
                  {verificationStatus.emailVerified ? 'Verified' : 'Not Verified'}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-brand-dark/40 border border-white/5">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-brand-textMuted uppercase tracking-wider">Identity Verification</span>
                  {verificationStatus.identityVerified ? (
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-amber-400" />
                  )}
                </div>
                <span className={`text-xs font-semibold ${verificationStatus.identityVerified ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {verificationStatus.identityVerified ? 'Verified' : 'Pending'}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-brand-dark/40 border border-white/5">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-brand-textMuted uppercase tracking-wider">Professional Verification</span>
                  {verificationStatus.professionalVerified ? (
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-amber-400" />
                  )}
                </div>
                <span className={`text-xs font-semibold ${verificationStatus.professionalVerified ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {verificationStatus.professionalVerified ? 'Verified' : 'Pending'}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-brand-dark/40 border border-white/5">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-brand-textMuted uppercase tracking-wider">Profile Completion</span>
                  <span className="text-xs font-bold text-brand-blue">{verificationStatus.profileCompletion}%</span>
                </div>
                <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-brand-blue to-brand-purple rounded-full transition-all duration-500"
                    style={{ width: `${verificationStatus.profileCompletion}%` }}
                  />
                </div>
              </div>
            </div>
          </motion.div>

          {/* Professional Information Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="rounded-2xl bg-brand-dark/30 border border-white/5 p-6 shadow-premium-card"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-white font-display flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-brand-purple" />
                Professional Information
              </h3>
              <button
                onClick={handleOpenEditModal}
                className="text-brand-blue text-xs font-semibold hover:text-brand-blue/80 transition-colors"
              >
                <Edit className="w-3 h-3" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-brand-textMuted">Role</span>
                <p className="text-sm text-white font-medium capitalize">{userRole}</p>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-brand-textMuted">Organization</span>
                <p className="text-sm text-white font-medium">{organizationName}</p>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-brand-textMuted">Specialization</span>
                <p className="text-sm text-white font-medium">{profileData.specialization || 'Not specified'}</p>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-brand-textMuted">Jurisdiction</span>
                <p className="text-sm text-white font-medium">{profileData.jurisdiction || 'Not specified'}</p>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-brand-textMuted">Bar Registration Number</span>
                <p className="text-sm text-white font-medium">{profileData.barNumber || 'Not specified'}</p>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-brand-textMuted">Years of Experience</span>
                <p className="text-sm text-white font-medium">{profileData.yearsOfExperience || 'Not specified'}</p>
              </div>

              <div className="space-y-1 md:col-span-2">
                <span className="text-[10px] uppercase tracking-wider text-brand-textMuted">Contact</span>
                <p className="text-sm text-white font-medium">{userEmail}</p>
                {profileData.phone && <p className="text-sm text-white font-medium">{profileData.phone}</p>}
              </div>
            </div>
          </motion.div>

          {/* About Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.3 }}
            className="rounded-2xl bg-brand-dark/30 border border-white/5 p-6 shadow-premium-card"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-white font-display flex items-center gap-2">
                <FileText className="w-4 h-4 text-brand-blue" />
                About
              </h3>
              <button
                onClick={handleOpenEditModal}
                className="text-brand-blue text-xs font-semibold hover:text-brand-blue/80 transition-colors"
              >
                <Edit className="w-3 h-3" />
              </button>
            </div>

            {profileData.bio ? (
              <p className="text-sm text-brand-textMuted/80 leading-relaxed">{profileData.bio}</p>
            ) : (
              <div className="text-center py-8 border-2 border-dashed border-white/10 rounded-xl">
                <FileText className="w-8 h-8 text-brand-textMuted/30 mx-auto mb-2" />
                <p className="text-xs text-brand-textMuted/60 mb-3">No bio added yet</p>
                <button
                  onClick={handleOpenEditModal}
                  className="text-brand-blue text-xs font-semibold hover:text-brand-blue/80 transition-colors"
                >
                  Add your bio
                </button>
              </div>
            )}
          </motion.div>
        </div>

        {/* Right Column - Activity Stats & Recent Activity */}
        <div className="space-y-6">
          {/* Activity Statistics */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.4 }}
            className="rounded-2xl bg-brand-dark/30 border border-white/5 p-6 shadow-premium-card"
          >
            <h3 className="text-sm font-bold uppercase tracking-wider text-white font-display flex items-center gap-2 mb-4">
              <TrendingUp className="w-4 h-4 text-brand-purple" />
              Platform Activity
            </h3>

            <div className="space-y-3">
              <div className="p-3 rounded-xl border border-white/5 bg-brand-dark/40 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-brand-blue/10 border border-brand-blue/20">
                    <FolderOpen className="w-4 h-4 text-brand-blue" />
                  </div>
                  <span className="text-xs text-brand-textMuted">Cases Created</span>
                </div>
                <span className="text-lg font-bold text-white">{activityStats.casesCreated}</span>
              </div>

              <div className="p-3 rounded-xl border border-white/5 bg-brand-dark/40 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-brand-purple/10 border border-brand-purple/20">
                    <Scale className="w-4 h-4 text-brand-purple" />
                  </div>
                  <span className="text-xs text-brand-textMuted">Cases Analyzed</span>
                </div>
                <span className="text-lg font-bold text-white">{activityStats.casesAnalyzed}</span>
              </div>

              <div className="p-3 rounded-xl border border-white/5 bg-brand-dark/40 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                    <FileCheck className="w-4 h-4 text-emerald-400" />
                  </div>
                  <span className="text-xs text-brand-textMuted">Reports Generated</span>
                </div>
                <span className="text-lg font-bold text-white">{activityStats.reportsGenerated}</span>
              </div>

              <div className="p-3 rounded-xl border border-white/5 bg-brand-dark/40 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
                    <Zap className="w-4 h-4 text-amber-400" />
                  </div>
                  <span className="text-xs text-brand-textMuted">AI Analyses</span>
                </div>
                <span className="text-lg font-bold text-white">{activityStats.aiAnalysesPerformed}</span>
              </div>
            </div>
          </motion.div>

          {/* Recent Activity */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.5 }}
            className="rounded-2xl bg-brand-dark/30 border border-white/5 p-6 shadow-premium-card"
          >
            <h3 className="text-sm font-bold uppercase tracking-wider text-white font-display flex items-center gap-2 mb-4">
              <Clock className="w-4 h-4 text-brand-blue" />
              Recent Activity
            </h3>

            <div className="space-y-3">
              {recentActivity.map((activity, index) => (
                <div key={index} className="p-3 rounded-xl border border-white/5 bg-brand-dark/40">
                  <div className="flex items-start gap-3">
                    <div className={`p-1.5 rounded-lg ${
                      activity.type === 'case' ? 'bg-brand-blue/10' :
                      activity.type === 'report' ? 'bg-brand-purple/10' :
                      'bg-white/5'
                    }`}>
                      {activity.type === 'case' && <FolderOpen className="w-3 h-3 text-brand-blue" />}
                      {activity.type === 'report' && <FileCheck className="w-3 h-3 text-brand-purple" />}
                      {activity.type === 'login' && <Clock className="w-3 h-3 text-brand-textMuted" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-xs text-white font-medium">{activity.title}</p>
                      <p className="text-[10px] text-brand-textMuted/60 mt-0.5">{activity.time}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Account Info */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.6 }}
            className="rounded-2xl bg-brand-dark/30 border border-white/5 p-6 shadow-premium-card"
          >
            <h3 className="text-sm font-bold uppercase tracking-wider text-white font-display flex items-center gap-2 mb-4">
              <Calendar className="w-4 h-4 text-brand-blue" />
              Account Information
            </h3>

            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-xs text-brand-textMuted">Member Since</span>
                <span className="text-xs text-white font-medium">June 2026</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/5">
                <span className="text-xs text-brand-textMuted">Account Type</span>
                <span className="text-xs text-white font-medium">Professional</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-xs text-brand-textMuted">Status</span>
                <span className="text-xs text-emerald-400 font-medium">Active</span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Edit Profile Modal */}
      <AnimatePresence>
        {isEditModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setIsEditModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-brand-dark/95 border border-white/10 rounded-2xl p-6 w-full max-w-lg shadow-premium-card"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-white font-display">Edit Profile</h3>
                <button
                  onClick={() => setIsEditModalOpen(false)}
                  className="text-brand-textMuted hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs text-brand-textMuted mb-1">Phone Number</label>
                  <input
                    type="tel"
                    value={editFormData.phone}
                    onChange={(e) => setEditFormData({ ...editFormData, phone: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-brand-dark/50 border border-white/10 text-white text-sm focus:border-brand-blue/50 focus:outline-none"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>

                <div>
                  <label className="block text-xs text-brand-textMuted mb-1">Specialization</label>
                  <input
                    type="text"
                    value={editFormData.specialization}
                    onChange={(e) => setEditFormData({ ...editFormData, specialization: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-brand-dark/50 border border-white/10 text-white text-sm focus:border-brand-blue/50 focus:outline-none"
                    placeholder="e.g., Corporate Law, Criminal Defense"
                  />
                </div>

                <div>
                  <label className="block text-xs text-brand-textMuted mb-1">Bar Registration Number</label>
                  <input
                    type="text"
                    value={editFormData.barNumber}
                    onChange={(e) => setEditFormData({ ...editFormData, barNumber: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-brand-dark/50 border border-white/10 text-white text-sm focus:border-brand-blue/50 focus:outline-none"
                    placeholder="e.g., BAR-12345"
                  />
                </div>

                <div>
                  <label className="block text-xs text-brand-textMuted mb-1">Jurisdiction</label>
                  <input
                    type="text"
                    value={editFormData.jurisdiction}
                    onChange={(e) => setEditFormData({ ...editFormData, jurisdiction: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-brand-dark/50 border border-white/10 text-white text-sm focus:border-brand-blue/50 focus:outline-none"
                    placeholder="e.g., California, New York"
                  />
                </div>

                <div>
                  <label className="block text-xs text-brand-textMuted mb-1">Years of Experience</label>
                  <input
                    type="number"
                    value={editFormData.yearsOfExperience}
                    onChange={(e) => setEditFormData({ ...editFormData, yearsOfExperience: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-[#161f30]/65 border border-white/10 text-white text-sm focus:border-brand-blue/50 focus:outline-none"
                    placeholder="e.g., 10"
                    min="0"
                  />
                </div>

                <div>
                  <label className="block text-xs text-brand-textMuted mb-1">Bio</label>
                  <textarea
                    value={editFormData.bio}
                    onChange={(e) => setEditFormData({ ...editFormData, bio: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-[#161f30]/65 border border-white/10 text-white text-sm focus:border-brand-blue/50 focus:outline-none resize-none"
                    placeholder="Tell us about yourself..."
                    rows={4}
                    maxLength={500}
                  />
                  <div className="text-right text-[10px] text-brand-textMuted mt-1">
                    {editFormData.bio.length}/500
                  </div>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setIsEditModalOpen(false)}
                  className="flex-1 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm font-semibold hover:bg-white/10 transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveProfile}
                  className="flex-1 px-4 py-2 rounded-xl bg-brand-blue text-white text-sm font-semibold hover:bg-brand-blue/80 transition-all flex items-center justify-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  Save Changes
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Photo Management Modal */}
      <AnimatePresence>
        {isPhotoModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setIsPhotoModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-brand-dark/95 border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-premium-card"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-white font-display">Profile Photo</h3>
                <button
                  onClick={() => setIsPhotoModalOpen(false)}
                  className="text-brand-textMuted hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Photo Preview */}
              <div className="flex justify-center mb-6">
                <div className="relative">
                  {photoPreview ? (
                    <div className="w-32 h-32 rounded-full border-2 border-brand-blue/30 bg-brand-dark overflow-hidden">
                      <img src={photoPreview} alt="Preview" className="w-full h-full object-cover" />
                    </div>
                  ) : (
                    <div className="w-32 h-32 rounded-full border-2 border-brand-blue/30 bg-brand-dark flex items-center justify-center">
                      <ImageIcon className="w-12 h-12 text-brand-textMuted" />
                    </div>
                  )}
                </div>
              </div>

              {/* Upload Button */}
              <div className="mb-4">
                <input
                  type="file"
                  accept="image/jpeg,image/jpg,image/png,image/webp"
                  onChange={handlePhotoSelect}
                  className="hidden"
                  id="photo-upload-modal"
                />
                <label
                  htmlFor="photo-upload-modal"
                  className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl bg-brand-blue/10 border border-brand-blue/20 text-brand-blue text-sm font-semibold hover:bg-brand-blue/20 transition-all cursor-pointer"
                >
                  <Upload className="w-4 h-4" />
                  Upload New Photo
                </label>
              </div>

              {/* Actions */}
              <div className="space-y-3">
                <button
                  onClick={handleSavePhoto}
                  disabled={!photoPreview}
                  className="w-full px-4 py-2 rounded-xl bg-brand-blue text-white text-sm font-semibold hover:bg-brand-blue/80 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  Save Photo
                </button>

                {profileData.profilePhoto && (
                  <button
                    onClick={handleRemovePhoto}
                    className="w-full px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-semibold hover:bg-red-500/20 transition-all flex items-center justify-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Remove Photo
                  </button>
                )}
              </div>

              <p className="text-[10px] text-brand-textMuted text-center mt-4">
                Supported formats: JPG, JPEG, PNG, WEBP (Max 5MB)
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
