import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Container,
  Typography,
  Button,
  TextField,
  Card,
  CardContent,
  InputAdornment,
  Alert,
  IconButton,
  Stack,
  Chip,
  Paper,
  Grid,
  useTheme,
  useMediaQuery,
} from "@mui/material";
import {
  Business,
  ArrowForward,
  CheckCircle,
  Speed,
  Security,
  CloudQueue,
  Group,
  Dashboard,
  Settings,
  TrendingUp,
  Star,
  Domain,
} from "@mui/icons-material";
import { redirectToTenantSubdomain } from "../../utils/api";

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const [tenantSlug, setTenantSlug] = useState("");
  const [error, setError] = useState("");

  const handleTenantAccess = () => {
    if (!tenantSlug.trim()) {
      setError("Please enter your organization's subdomain");
      return;
    }

    // Validate slug format (alphanumeric and hyphens only)
    if (!/^[a-z0-9-]+$/.test(tenantSlug)) {
      setError(
        "Subdomain can only contain lowercase letters, numbers, and hyphens",
      );
      return;
    }

    // Redirect to tenant subdomain
    redirectToTenantSubdomain(tenantSlug, "/auth/login");
  };

  const features = [
    {
      icon: <Speed />,
      title: "Lightning Fast",
      description: "Built for performance and scalability from day one",
    },
    {
      icon: <Security />,
      title: "Enterprise Security",
      description: "Bank-level security with data isolation for each tenant",
    },
    {
      icon: <CloudQueue />,
      title: "Cloud Native",
      description: "Fully cloud-based solution with 99.9% uptime SLA",
    },
    {
      icon: <Group />,
      title: "Team Collaboration",
      description: "Invite unlimited team members and manage permissions",
    },
    {
      icon: <Dashboard />,
      title: "Powerful Analytics",
      description: "Real-time insights and customizable dashboards",
    },
    {
      icon: <Settings />,
      title: "Fully Customizable",
      description: "Tailor the platform to your specific needs",
    },
  ];

  const testimonials = [
    {
      name: "Sarah Johnson",
      role: "CEO, TechCorp",
      content:
        "This platform has transformed how we manage our business. The multi-tenant architecture is exactly what we needed.",
      rating: 5,
    },
    {
      name: "Michael Chen",
      role: "CTO, StartupXYZ",
      content:
        "Incredible performance and reliability. We've scaled from 10 to 1000 users without any issues.",
      rating: 5,
    },
    {
      name: "Emily Rodriguez",
      role: "Product Manager, InnovateCo",
      content:
        "The best SaaS platform we've used. Feature-rich and intuitive interface.",
      rating: 5,
    },
  ];

  const pricingPlans = [
    {
      name: "Starter",
      price: "$29",
      period: "per month",
      features: [
        "Up to 10 users",
        "5GB storage",
        "Basic support",
        "Core features",
      ],
      highlighted: false,
    },
    {
      name: "Professional",
      price: "$99",
      period: "per month",
      features: [
        "Up to 50 users",
        "50GB storage",
        "Priority support",
        "Advanced features",
        "API access",
      ],
      highlighted: true,
    },
    {
      name: "Enterprise",
      price: "Custom",
      period: "contact us",
      features: [
        "Unlimited users",
        "Unlimited storage",
        "24/7 dedicated support",
        "Custom features",
        "SLA guarantee",
      ],
      highlighted: false,
    },
  ];

  return (
    <Box sx={{ minHeight: "100vh" }}>
      {/* Hero Section */}
      <Box
        sx={{
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          color: "white",
          py: { xs: 8, md: 12 },
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={4} alignItems="center">
            <Grid size={{ xs: 12, md: 6 }}>
              <Typography
                variant="h2"
                component="h1"
                gutterBottom
                sx={{
                  fontWeight: 700,
                  fontSize: { xs: "2.5rem", md: "3.5rem" },
                }}
              >
                Your Business, Elevated
              </Typography>
              <Typography variant="h5" sx={{ mb: 4, opacity: 0.9 }}>
                Powerful multi-tenant SaaS platform to manage and scale your
                business effortlessly
              </Typography>
              <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => navigate("/auth/register")}
                  sx={{
                    bgcolor: "white",
                    color: "primary.main",
                    "&:hover": { bgcolor: "grey.100" },
                  }}
                >
                  Start Free Trial
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => navigate("/pricing")}
                  sx={{
                    borderColor: "white",
                    color: "white",
                    "&:hover": {
                      borderColor: "white",
                      bgcolor: "rgba(255,255,255,0.1)",
                    },
                  }}
                >
                  View Pricing
                </Button>
              </Stack>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Paper
                elevation={3}
                sx={{
                  p: 4,
                  borderRadius: 2,
                  background: "rgba(255,255,255,0.95)",
                }}
              >
                <Typography
                  variant="h6"
                  gutterBottom
                  sx={{ color: "text.primary", fontWeight: 600 }}
                >
                  Access Your Organization
                </Typography>
                <Typography
                  variant="body2"
                  sx={{ color: "text.secondary", mb: 3 }}
                >
                  Enter your organization's subdomain to access your workspace
                </Typography>
                {error && (
                  <Alert
                    severity="error"
                    sx={{ mb: 2 }}
                    onClose={() => setError("")}
                  >
                    {error}
                  </Alert>
                )}
                <Box sx={{ display: "flex", gap: 1 }}>
                  <TextField
                    fullWidth
                    placeholder="your-organization"
                    value={tenantSlug}
                    onChange={(e) => {
                      setTenantSlug(e.target.value.toLowerCase());
                      setError("");
                    }}
                    onKeyPress={(e) => {
                      if (e.key === "Enter") {
                        handleTenantAccess();
                      }
                    }}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Domain />
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <Typography variant="body2" color="text.secondary">
                            .localhost:3000
                          </Typography>
                        </InputAdornment>
                      ),
                    }}
                  />
                  <IconButton
                    color="primary"
                    onClick={handleTenantAccess}
                    sx={{
                      bgcolor: "primary.main",
                      color: "white",
                      "&:hover": { bgcolor: "primary.dark" },
                    }}
                  >
                    <ArrowForward />
                  </IconButton>
                </Box>
                <Typography
                  variant="caption"
                  sx={{ color: "text.secondary", mt: 1, display: "block" }}
                >
                  Example: tenant1, tenant2, etc.
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography
          variant="h3"
          align="center"
          gutterBottom
          sx={{ fontWeight: 600 }}
        >
          Everything You Need to Succeed
        </Typography>
        <Typography
          variant="h6"
          align="center"
          color="text.secondary"
          sx={{ mb: 6 }}
        >
          Powerful features designed for modern businesses
        </Typography>
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={index}>
              <Card
                sx={{
                  height: "100%",
                  transition: "transform 0.2s",
                  "&:hover": { transform: "translateY(-4px)" },
                }}
              >
                <CardContent sx={{ textAlign: "center", p: 3 }}>
                  <Box
                    sx={{
                      display: "inline-flex",
                      p: 2,
                      borderRadius: "50%",
                      bgcolor: "primary.light",
                      color: "white",
                      mb: 2,
                    }}
                  >
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" gutterBottom>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Pricing Section */}
      <Box sx={{ bgcolor: "grey.50", py: 8 }}>
        <Container maxWidth="lg">
          <Typography
            variant="h3"
            align="center"
            gutterBottom
            sx={{ fontWeight: 600 }}
          >
            Simple, Transparent Pricing
          </Typography>
          <Typography
            variant="h6"
            align="center"
            color="text.secondary"
            sx={{ mb: 6 }}
          >
            Choose the plan that fits your needs
          </Typography>
          <Grid container spacing={4} justifyContent="center">
            {pricingPlans.map((plan, index) => (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={index}>
                <Card
                  raised={plan.highlighted}
                  sx={{
                    height: "100%",
                    position: "relative",
                    border: plan.highlighted ? "2px solid" : "1px solid",
                    borderColor: plan.highlighted ? "primary.main" : "grey.300",
                  }}
                >
                  {plan.highlighted && (
                    <Chip
                      label="Most Popular"
                      color="primary"
                      sx={{
                        position: "absolute",
                        top: -12,
                        left: "50%",
                        transform: "translateX(-50%)",
                      }}
                    />
                  )}
                  <CardContent sx={{ p: 4, textAlign: "center" }}>
                    <Typography
                      variant="h5"
                      gutterBottom
                      sx={{ fontWeight: 600 }}
                    >
                      {plan.name}
                    </Typography>
                    <Typography
                      variant="h3"
                      gutterBottom
                      sx={{ fontWeight: 700 }}
                    >
                      {plan.price}
                    </Typography>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 3 }}
                    >
                      {plan.period}
                    </Typography>
                    <Stack spacing={2} sx={{ mb: 4 }}>
                      {plan.features.map((feature, idx) => (
                        <Box
                          key={idx}
                          sx={{ display: "flex", alignItems: "center", gap: 1 }}
                        >
                          <CheckCircle color="success" fontSize="small" />
                          <Typography variant="body2">{feature}</Typography>
                        </Box>
                      ))}
                    </Stack>
                    <Button
                      fullWidth
                      variant={plan.highlighted ? "contained" : "outlined"}
                      size="large"
                      onClick={() => navigate("/auth/register")}
                    >
                      Get Started
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Testimonials Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography
          variant="h3"
          align="center"
          gutterBottom
          sx={{ fontWeight: 600 }}
        >
          Loved by Teams Worldwide
        </Typography>
        <Typography
          variant="h6"
          align="center"
          color="text.secondary"
          sx={{ mb: 6 }}
        >
          See what our customers have to say
        </Typography>
        <Grid container spacing={4}>
          {testimonials.map((testimonial, index) => (
            <Grid size={{ xs: 12, md: 4 }} key={index}>
              <Card sx={{ height: "100%" }}>
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: "flex", mb: 2 }}>
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star
                        key={i}
                        sx={{ color: "warning.main", fontSize: 20 }}
                      />
                    ))}
                  </Box>
                  <Typography
                    variant="body1"
                    sx={{ mb: 2, fontStyle: "italic" }}
                  >
                    "{testimonial.content}"
                  </Typography>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    {testimonial.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {testimonial.role}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* CTA Section */}
      <Box
        sx={{
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          color: "white",
          py: 8,
        }}
      >
        <Container maxWidth="md" sx={{ textAlign: "center" }}>
          <Typography variant="h3" gutterBottom sx={{ fontWeight: 600 }}>
            Ready to Get Started?
          </Typography>
          <Typography variant="h6" sx={{ mb: 4, opacity: 0.9 }}>
            Join thousands of businesses already using our platform
          </Typography>
          <Stack
            direction={{ xs: "column", sm: "row" }}
            spacing={2}
            justifyContent="center"
          >
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate("/auth/register")}
              sx={{
                bgcolor: "white",
                color: "primary.main",
                px: 4,
                "&:hover": { bgcolor: "grey.100" },
              }}
              endIcon={<ArrowForward />}
            >
              Start Your Free Trial
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate("/contact")}
              sx={{
                borderColor: "white",
                color: "white",
                px: 4,
                "&:hover": {
                  borderColor: "white",
                  bgcolor: "rgba(255,255,255,0.1)",
                },
              }}
            >
              Contact Sales
            </Button>
          </Stack>
        </Container>
      </Box>

      {/* Footer */}
      <Box sx={{ bgcolor: "grey.900", color: "white", py: 4 }}>
        <Container maxWidth="lg">
          <Grid container spacing={4}>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="h6" gutterBottom>
                Multi-Tenant Platform
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.7 }}>
                Enterprise-grade SaaS platform for modern businesses
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="h6" gutterBottom>
                Quick Links
              </Typography>
              <Stack spacing={1}>
                <Typography
                  variant="body2"
                  sx={{
                    opacity: 0.7,
                    cursor: "pointer",
                    "&:hover": { opacity: 1 },
                  }}
                  onClick={() => navigate("/features")}
                >
                  Features
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    opacity: 0.7,
                    cursor: "pointer",
                    "&:hover": { opacity: 1 },
                  }}
                  onClick={() => navigate("/pricing")}
                >
                  Pricing
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    opacity: 0.7,
                    cursor: "pointer",
                    "&:hover": { opacity: 1 },
                  }}
                  onClick={() => navigate("/contact")}
                >
                  Contact
                </Typography>
              </Stack>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="h6" gutterBottom>
                Admin Access
              </Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate("/admin")}
                sx={{
                  borderColor: "white",
                  color: "white",
                  "&:hover": {
                    borderColor: "white",
                    bgcolor: "rgba(255,255,255,0.1)",
                  },
                }}
              >
                Admin Dashboard
              </Button>
            </Grid>
          </Grid>
          <Box
            sx={{
              mt: 4,
              pt: 4,
              borderTop: "1px solid rgba(255,255,255,0.1)",
              textAlign: "center",
            }}
          >
            <Typography variant="body2" sx={{ opacity: 0.7 }}>
              © 2024 Multi-Tenant Platform. All rights reserved.
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default LandingPage;
