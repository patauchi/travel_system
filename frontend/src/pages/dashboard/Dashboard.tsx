import React, { useEffect, useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  LinearProgress,
  IconButton,
  Divider,
  Alert,
  Skeleton,
  Grid,
} from "@mui/material";
import {
  TrendingUp,
  Person,
  Task,
  Folder,
  Storage,
  Settings,
  Add,
  ArrowForward,
  CheckCircle,
  Schedule,
  Warning,
  Notifications,
  Dashboard as DashboardIcon,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { useAppSelector } from "../../store/store";
import { format } from "date-fns";

interface StatCard {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
  color: string;
}

interface RecentActivity {
  id: string;
  type: string;
  description: string;
  timestamp: Date;
  user: string;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAppSelector((state) => state.auth);
  const { currentTenant } = useAppSelector((state) => state.tenant);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeTasks: 0,
    completedTasks: 0,
    storageUsed: 0,
    storageTotal: 0,
  });
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>(
    [],
  );

  useEffect(() => {
    // Simulate loading data
    setTimeout(() => {
      setStats({
        totalUsers: currentTenant?.user_count || 1,
        activeTasks: 12,
        completedTasks: 45,
        storageUsed: currentTenant?.storage_used_gb || 0,
        storageTotal: currentTenant?.max_storage_gb || 100,
      });
      setRecentActivities([
        {
          id: "1",
          type: "task",
          description: "New task created: Update documentation",
          timestamp: new Date(),
          user: "John Doe",
        },
        {
          id: "2",
          type: "user",
          description: "New user joined the team",
          timestamp: new Date(Date.now() - 3600000),
          user: "Jane Smith",
        },
        {
          id: "3",
          type: "file",
          description: "File uploaded: Q4_Report.pdf",
          timestamp: new Date(Date.now() - 7200000),
          user: "Mike Johnson",
        },
      ]);
      setLoading(false);
    }, 1000);
  }, [currentTenant]);

  const statCards: StatCard[] = [
    {
      title: "Total Users",
      value: `${stats.totalUsers}/${currentTenant?.max_users || 50}`,
      icon: <Person />,
      color: "#1976d2",
    },
    {
      title: "Active Tasks",
      value: stats.activeTasks,
      change: 15,
      icon: <Task />,
      color: "#ff9800",
    },
    {
      title: "Completed Tasks",
      value: stats.completedTasks,
      change: 8,
      icon: <CheckCircle />,
      color: "#4caf50",
    },
    {
      title: "Storage Used",
      value: `${stats.storageUsed} GB`,
      icon: <Storage />,
      color: "#9c27b0",
    },
  ];

  const quickActions = [
    {
      title: "Create Task",
      description: "Add a new task to your workflow",
      icon: <Add />,
      action: () => navigate("/dashboard/tasks"),
    },
    {
      title: "Invite User",
      description: "Add team members to collaborate",
      icon: <Person />,
      action: () => navigate("/dashboard/team"),
    },
    {
      title: "View Reports",
      description: "Check your analytics and reports",
      icon: <TrendingUp />,
      action: () => navigate("/dashboard/analytics"),
    },
    {
      title: "Settings",
      description: "Configure your workspace",
      icon: <Settings />,
      action: () => navigate("/dashboard/settings"),
    },
  ];

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "task":
        return <Task />;
      case "user":
        return <Person />;
      case "file":
        return <Folder />;
      default:
        return <Notifications />;
    }
  };

  const getTimeAgo = (date: Date) => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    if (seconds < 60) return "just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours > 1 ? "s" : ""} ago`;
    return format(date, "MMM d, yyyy");
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Welcome Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Welcome back, {user?.full_name || user?.username || "User"}! 👋
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {currentTenant ? (
            <>
              You're currently in <strong>{currentTenant.name}</strong>{" "}
              workspace. Here's your dashboard overview.
            </>
          ) : (
            "Loading your workspace information..."
          )}
        </Typography>
      </Box>

      {/* Subscription Alert */}
      {currentTenant?.status === "trial" && currentTenant.trial_ends_at && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            Your trial ends on{" "}
            {format(new Date(currentTenant.trial_ends_at), "MMMM d, yyyy")}.{" "}
            <Button
              size="small"
              onClick={() => navigate("/dashboard/tenant/billing")}
            >
              Upgrade Now
            </Button>
          </Typography>
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((stat, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
            {loading ? (
              <Card>
                <CardContent>
                  <Skeleton variant="rectangular" height={100} />
                </CardContent>
              </Card>
            ) : (
              <Card
                sx={{
                  transition: "transform 0.2s",
                  "&:hover": { transform: "translateY(-4px)" },
                }}
              >
                <CardContent>
                  <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                    <Avatar
                      sx={{
                        bgcolor: stat.color,
                        width: 48,
                        height: 48,
                      }}
                    >
                      {stat.icon}
                    </Avatar>
                    {stat.change && (
                      <Chip
                        label={`+${stat.change}%`}
                        size="small"
                        color="success"
                        sx={{ ml: "auto" }}
                      />
                    )}
                  </Box>
                  <Typography variant="h4" gutterBottom>
                    {stat.value}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {stat.title}
                  </Typography>
                </CardContent>
              </Card>
            )}
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Quick Actions */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Grid container spacing={2}>
                {quickActions.map((action, index) => (
                  <Grid size={{ xs: 12, sm: 6 }} key={index}>
                    <Paper
                      sx={{
                        p: 2,
                        cursor: "pointer",
                        transition: "all 0.2s",
                        "&:hover": {
                          bgcolor: "action.hover",
                          transform: "translateX(4px)",
                        },
                      }}
                      onClick={action.action}
                    >
                      <Box sx={{ display: "flex", alignItems: "center" }}>
                        <Avatar
                          sx={{
                            bgcolor: "primary.light",
                            mr: 2,
                          }}
                        >
                          {action.icon}
                        </Avatar>
                        <Box sx={{ flexGrow: 1 }}>
                          <Typography variant="subtitle1">
                            {action.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {action.description}
                          </Typography>
                        </Box>
                        <IconButton>
                          <ArrowForward />
                        </IconButton>
                      </Box>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>

          {/* Storage Usage */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Storage Usage
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    mb: 1,
                  }}
                >
                  <Typography variant="body2">
                    {stats.storageUsed} GB used of {stats.storageTotal} GB
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {Math.round((stats.storageUsed / stats.storageTotal) * 100)}
                    %
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={(stats.storageUsed / stats.storageTotal) * 100}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ height: "100%" }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              {loading ? (
                <Box>
                  {[1, 2, 3].map((item) => (
                    <Box key={item} sx={{ mb: 2 }}>
                      <Skeleton variant="rectangular" height={60} />
                    </Box>
                  ))}
                </Box>
              ) : (
                <List>
                  {recentActivities.map((activity, index) => (
                    <React.Fragment key={activity.id}>
                      <ListItem alignItems="flex-start" sx={{ px: 0 }}>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: "primary.light" }}>
                            {getActivityIcon(activity.type)}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={activity.description}
                          secondary={
                            <>
                              <Typography
                                component="span"
                                variant="body2"
                                color="text.primary"
                              >
                                {activity.user}
                              </Typography>
                              {" — "}
                              {getTimeAgo(activity.timestamp)}
                            </>
                          }
                        />
                      </ListItem>
                      {index < recentActivities.length - 1 && (
                        <Divider variant="inset" component="li" />
                      )}
                    </React.Fragment>
                  ))}
                </List>
              )}
              <Button
                fullWidth
                sx={{ mt: 2 }}
                onClick={() => navigate("/dashboard/activity")}
              >
                View All Activity
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tenant Information Card */}
      {currentTenant && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Workspace Information
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Workspace Name
                </Typography>
                <Typography variant="body1">{currentTenant.name}</Typography>
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Plan
                </Typography>
                <Chip
                  label={currentTenant.subscription_plan}
                  color="primary"
                  size="small"
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Status
                </Typography>
                <Chip
                  label={currentTenant.status}
                  color={
                    currentTenant.status === "active" ? "success" : "warning"
                  }
                  size="small"
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Created
                </Typography>
                <Typography variant="body1">
                  {format(new Date(currentTenant.created_at), "MMM d, yyyy")}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default Dashboard;
