import React from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';
import AuthContainer from '../components/Auth/AuthContainer';
import { useNavigate } from 'react-router-dom';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import SearchIcon from '@mui/icons-material/Search';
import BoltIcon from '@mui/icons-material/Bolt';

const AuthPage = () => {
  const navigate = useNavigate();

  const handleLoginSuccess = (userData) => {
    console.log("User logged in:", userData);
    navigate('/');
  };

  return (
    <Box sx={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      py: { xs: 2, sm: 3 },
      animation: 'fadeIn 0.8s ease-out',
      '@keyframes fadeIn': {
        '0%': { opacity: 0 },
        '100%': { opacity: 1 }
      },
    }}>
      <Container maxWidth="lg">
        <Box sx={{ 
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          zIndex: 1,
        }}>
          <Typography 
            variant="h3" 
            component="h1" 
            fontWeight="700" 
            sx={{ 
              mb: 3,
              letterSpacing: '0.5px',
              textAlign: 'center',
              background: 'linear-gradient(45deg, #7FE786, #58A7FE)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative'
            }}
          >
            <AutoAwesomeIcon 
              sx={{ 
                mr: 1,
                fontSize: 30, 
                color: '#58A7FE',
                filter: 'drop-shadow(0 2px 5px rgba(88, 167, 254, 0.3))'
              }} 
            />
            Sema
          </Typography>

          <Paper
            elevation={0}
            sx={{
              p: { xs: 2.5, sm: 3 },
              mb: 4,
              maxWidth: 600,
              width: '100%',
              bgcolor: 'rgba(255, 255, 255, 0.95)',
              borderRadius: 3,
              backdropFilter: 'blur(10px)',
              boxShadow: '0 10px 25px rgba(0, 0, 0, 0.08)',
              position: 'relative',
              overflow: 'hidden',
              animation: 'slideUp 0.6s ease-out',
              animationDelay: '0.2s',
              animationFillMode: 'both',
              '@keyframes slideUp': {
                '0%': { transform: 'translateY(30px)', opacity: 0 },
                '100%': { transform: 'translateY(0)', opacity: 1 }
              },
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '3px',
                background: 'linear-gradient(90deg, #7FE786, #58A7FE)',
              }
            }}
          >
            <Typography 
              variant="h5" 
              align="center"
              sx={{ 
                fontWeight: 600,
                mb: 2,
                color: '#2d3748'
              }}
            >
              Welcome to Sema
            </Typography>
            
            <Box 
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                gap: 3,
                mb: 2
              }}
            >
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1
              }}>
                <CloudUploadIcon sx={{ color: '#7FE786' }} />
                <Typography variant="body2" fontWeight={500}>Upload</Typography>
              </Box>
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1
              }}>
                <SearchIcon sx={{ color: '#58A7FE' }} />
                <Typography variant="body2" fontWeight={500}>Search</Typography>
              </Box>
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center',
                gap: 1
              }}>
                <BoltIcon sx={{ color: '#7FE786' }} />
                <Typography variant="body2" fontWeight={500}>Analyze</Typography>
              </Box>
            </Box>
            
            <Typography 
              variant="body2" 
              align="center"
              sx={{
                fontWeight: 500,
                py: 1,
                borderTop: '1px solid rgba(0,0,0,0.06)',
                color: '#455a64'
              }}
            >
              Please log in or create an account to continue
            </Typography>
          </Paper>

          <Box sx={{
            animation: 'fadeInUp 0.8s ease-out',
            animationDelay: '0.3s',
            animationFillMode: 'both',
            width: '100%',
            maxWidth: 420,
            mb: 3,
            '@keyframes fadeInUp': {
              '0%': { transform: 'translateY(30px)', opacity: 0 },
              '100%': { transform: 'translateY(0)', opacity: 1 }
            }
          }}>
            <AuthContainer onLoginSuccess={handleLoginSuccess} />
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default AuthPage;