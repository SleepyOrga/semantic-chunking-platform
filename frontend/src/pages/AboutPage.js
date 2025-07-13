// src/pages/AboutPage.js
import React from 'react';
import { Container, Typography, Box, Paper, Avatar, Grid, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import GitHubIcon from '@mui/icons-material/GitHub';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import WebIcon from '@mui/icons-material/Web';

// Team member data
const teamMembers = [
  {
    name: 'Alex Johnson',
    role: 'Lead Developer',
    avatar: 'https://randomuser.me/api/portraits/men/32.jpg',
    bio: 'Full-stack developer with expertise in NLP and vector databases.',
    github: 'https://github.com/',
    linkedin: 'https://linkedin.com/'
  },
  {
    name: 'Sarah Chen',
    role: 'AI Engineer',
    avatar: 'https://randomuser.me/api/portraits/women/44.jpg',
    bio: 'Specializes in embedding models and semantic search algorithms.',
    github: 'https://github.com/',
    linkedin: 'https://linkedin.com/'
  },
  {
    name: 'Michael Rodriguez',
    role: 'UX Designer',
    avatar: 'https://randomuser.me/api/portraits/men/68.jpg',
    bio: 'Creates intuitive interfaces for complex data-driven applications.',
    github: 'https://github.com/',
    linkedin: 'https://linkedin.com/'
  },
  {
    name: 'Priya Patel',
    role: 'DevOps Engineer',
    avatar: 'https://randomuser.me/api/portraits/women/65.jpg',
    bio: 'Manages infrastructure and ensures smooth deployment processes.',
    github: 'https://github.com/',
    linkedin: 'https://linkedin.com/'
  }
];

const AboutPage = () => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      {/* Header */}
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center',
          mb: 6
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <AutoAwesomeIcon sx={{ fontSize: 40, color: '#6e41e2', mr: 1 }} />
          <Typography variant="h3" component="h1" fontWeight="500">
            Semantic Search Platform
          </Typography>
        </Box>
        <Typography variant="h6" color="text.secondary" align="center" sx={{ maxWidth: 700 }}>
          Advanced document search powered by AI embedding technology
        </Typography>
      </Box>

      {/* About the Project */}
      <Paper elevation={0} sx={{ p: 4, mb: 6, borderRadius: 2 }}>
        <Typography variant="h4" component="h2" gutterBottom>
          About the Project
        </Typography>
        <Typography variant="body1" paragraph>
          The Semantic Chunking Platform is an advanced document management system that uses 
          AI to understand the meaning behind your documents. Unlike traditional keyword search, 
          our platform uses semantic understanding to find information based on meaning rather than 
          exact word matches.
        </Typography>
        <Typography variant="body1" paragraph>
          Our platform automatically chunks your documents into meaningful segments, creates 
          vector embeddings for each chunk, and allows you to search through your documents using 
          natural language queries. This makes finding information in large document collections 
          faster and more accurate.
        </Typography>
        <Typography variant="body1" paragraph>
          Key features include:
        </Typography>
        <ul>
          <li>
            <Typography variant="body1">
              <strong>Semantic Search:</strong> Find information based on meaning, not just keywords
            </Typography>
          </li>
          <li>
            <Typography variant="body1">
              <strong>Document Chunking:</strong> Automatically divide documents into meaningful segments
            </Typography>
          </li>
          <li>
            <Typography variant="body1">
              <strong>Vector Embeddings:</strong> State-of-the-art AI models to understand document content
            </Typography>
          </li>
          <li>
            <Typography variant="body1">
              <strong>Fast Retrieval:</strong> Optimized for speed using pgvector and HNSW indexes
            </Typography>
          </li>
        </ul>
      </Paper>

      {/* Technology Stack */}
      <Paper elevation={0} sx={{ p: 4, mb: 6, borderRadius: 2 }}>
        <Typography variant="h4" component="h2" gutterBottom>
          Technology Stack
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Frontend</Typography>
              <Typography variant="body2" component="div">
                <ul>
                  <li>React</li>
                  <li>Material UI</li>
                  <li>Axios</li>
                  <li>React Router</li>
                </ul>
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Backend</Typography>
              <Typography variant="body2" component="div">
                <ul>
                  <li>Node.js</li>
                  <li>NestJS</li>
                  <li>PostgreSQL with pgvector</li>
                  <li>RabbitMQ</li>
                </ul>
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>AI/ML</Typography>
              <Typography variant="body2" component="div">
                <ul>
                  <li>OpenAI Embeddings</li>
                  <li>Vector Similarity Search</li>
                  <li>Document Chunking Algorithms</li>
                  <li>Semantic Tagging</li>
                </ul>
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Team Section */}
      <Typography variant="h4" component="h2" gutterBottom>
        Meet Our Team
      </Typography>
      <Grid container spacing={3} sx={{ mb: 6 }}>
        {teamMembers.map((member, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Paper 
              elevation={0} 
              sx={{ 
                p: 3, 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center',
                borderRadius: 2
              }}
            >
              <Avatar 
                src={member.avatar} 
                alt={member.name}
                sx={{ width: 100, height: 100, mb: 2 }}
              />
              <Typography variant="h6" gutterBottom>
                {member.name}
              </Typography>
              <Typography variant="subtitle1" color="primary" gutterBottom>
                {member.role}
              </Typography>
              <Typography variant="body2" paragraph sx={{ flexGrow: 1 }}>
                {member.bio}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <IconButton href={member.github} target="_blank" rel="noopener" GitHubIcon={GitHubIcon} />
                <IconButton href={member.linkedin} target="_blank" rel="noopener" LinkedInIcon={LinkedInIcon} />
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>

      {/* CTA */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Ready to try our platform?
        </Typography>
        <Button 
          variant="contained" 
          size="large"
          onClick={() => navigate('/')}
          sx={{ 
            mt: 2,
            bgcolor: '#6e41e2',
            '&:hover': { bgcolor: '#5a32c5' },
            py: 1.5,
            px: 4
          }}
        >
          Get Started
        </Button>
      </Box>
    </Container>
  );
};

// Helper component for social icons
const IconButton = ({ href, children, GitHubIcon, LinkedInIcon }) => (
  <Button
    variant="outlined"
    size="small"
    href={href}
    target="_blank"
    rel="noopener noreferrer"
    sx={{ 
      minWidth: 'auto',
      p: 1,
      borderRadius: '50%'
    }}
  >
    {GitHubIcon && <GitHubIcon fontSize="small" />}
    {LinkedInIcon && <LinkedInIcon fontSize="small" />}
    {children}
  </Button>
);

export default AboutPage;