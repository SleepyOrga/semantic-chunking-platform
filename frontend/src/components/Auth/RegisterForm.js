// src/components/Auth/RegisterForm.js
import React, { useState } from 'react';
import { TextField, Button, Typography, Box, CircularProgress, Alert } from '@mui/material';
import AuthService from '../../services/AuthService';

const RegisterForm = ({ onRegisterSuccess }) => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Form validation
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await AuthService.register(email, password, fullName);
      setSuccess(true);
      setTimeout(() => {
        onRegisterSuccess();
      }, 2000);
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>Registration successful! You can now sign in.</Alert>}
      
      <TextField
        margin="normal"
        required
        fullWidth
        id="fullName"
        label="Full Name"
        name="fullName"
        autoComplete="name"
        autoFocus
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
        disabled={loading || success}
      />
      
      <TextField
        margin="normal"
        required
        fullWidth
        id="email"
        label="Email Address"
        name="email"
        autoComplete="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        disabled={loading || success}
      />
      
      <TextField
        margin="normal"
        required
        fullWidth
        name="password"
        label="Password"
        type="password"
        id="password"
        autoComplete="new-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        disabled={loading || success}
      />
      
      <TextField
        margin="normal"
        required
        fullWidth
        name="confirmPassword"
        label="Confirm Password"
        type="password"
        id="confirmPassword"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        disabled={loading || success}
        error={password !== confirmPassword && confirmPassword !== ''}
        helperText={password !== confirmPassword && confirmPassword !== '' ? 'Passwords do not match' : ''}
      />
      
      <Button
        type="submit"
        fullWidth
        variant="contained"
        sx={{ 
          mt: 3, 
          mb: 2,
          bgcolor: '#6e41e2',
          '&:hover': { bgcolor: '#5a32c5' },
          py: 1.5
        }}
        disabled={loading || success}
      >
        {loading ? <CircularProgress size={24} color="inherit" /> : 'Sign Up'}
      </Button>
      
      <Typography variant="body2" align="center" sx={{ mt: 2 }}>
        Already have an account? Use the Login tab above.
      </Typography>
    </Box>
  );
};

export default RegisterForm;