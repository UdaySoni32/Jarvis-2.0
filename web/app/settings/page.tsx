'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';
import { apiClient } from '@/lib/api/client';
import { ArrowLeft, Cpu, HardDrive, Activity } from 'lucide-react';

export default function SettingsPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [status, setStatus] = useState<any>(null);
  const [models, setModels] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
      return;
    }

    const fetchData = async () => {
      try {
        const [statusData, modelsData] = await Promise.all([
          apiClient.getSystemStatus(),
          apiClient.getModels(),
        ]);
        setStatus(statusData);
        setModels(modelsData);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [isAuthenticated, router]);

  const handleSwitchModel = async (modelName: string) => {
    try {
      await apiClient.switchModel(modelName);
      const modelsData = await apiClient.getModels();
      setModels(modelsData);
    } catch (error) {
      console.error('Error switching model:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">⚙️</div>
          <p className="text-muted-foreground">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-white/50 dark:hover:bg-gray-800/50 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-3xl font-bold">Settings</h1>
            <p className="text-muted-foreground">Manage your JARVIS configuration</p>
          </div>
        </div>

        {/* User Info */}
        <div className="p-6 bg-white dark:bg-gray-800 rounded-xl shadow-lg">
          <h2 className="text-xl font-semibold mb-4">Account</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Username:</span>
              <span className="font-medium">{user?.username}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Email:</span>
              <span className="font-medium">{user?.email}</span>
            </div>
            {user?.full_name && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Name:</span>
                <span className="font-medium">{user.full_name}</span>
              </div>
            )}
          </div>
        </div>

        {/* System Status */}
        {status && (
          <div className="p-6 bg-white dark:bg-gray-800 rounded-xl shadow-lg">
            <h2 className="text-xl font-semibold mb-4">System Status</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Cpu className="w-5 h-5 text-blue-600" />
                  <span className="font-medium">CPU</span>
                </div>
                <div className="text-2xl font-bold">{status.resources.cpu_percent}%</div>
                <div className="text-sm text-muted-foreground">{status.resources.cpu_count} cores</div>
              </div>

              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-5 h-5 text-green-600" />
                  <span className="font-medium">Memory</span>
                </div>
                <div className="text-2xl font-bold">{status.resources.memory_percent}%</div>
                <div className="text-sm text-muted-foreground">
                  {status.resources.memory_used_gb} / {status.resources.memory_total_gb} GB
                </div>
              </div>

              <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <HardDrive className="w-5 h-5 text-purple-600" />
                  <span className="font-medium">Disk</span>
                </div>
                <div className="text-2xl font-bold">{status.resources.disk_percent}%</div>
                <div className="text-sm text-muted-foreground">
                  {status.resources.disk_used_gb} / {status.resources.disk_total_gb} GB
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Models */}
        {models && (
          <div className="p-6 bg-white dark:bg-gray-800 rounded-xl shadow-lg">
            <h2 className="text-xl font-semibold mb-4">AI Models</h2>
            <div className="space-y-3">
              <div className="p-3 bg-primary/10 rounded-lg">
                <div className="text-sm text-muted-foreground mb-1">Current Model</div>
                <div className="font-semibold text-lg">{models.current_model}</div>
              </div>

              <div className="space-y-2">
                {Object.entries(models.providers).map(([key, provider]: [string, any]) => (
                  provider.available && (
                    <details key={key} className="group">
                      <summary className="cursor-pointer p-3 bg-accent rounded-lg hover:bg-accent/80 transition-colors list-none">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{provider.name}</span>
                          <span className="text-sm text-muted-foreground">{provider.models.length} models</span>
                        </div>
                      </summary>
                      <div className="mt-2 ml-4 space-y-1">
                        {provider.models.map((model: string) => (
                          <button
                            key={model}
                            onClick={() => handleSwitchModel(model)}
                            className={`w-full text-left p-2 rounded-lg hover:bg-accent transition-colors ${
                              model === models.current_model ? 'bg-primary/10 text-primary' : ''
                            }`}
                          >
                            {model}
                          </button>
                        ))}
                      </div>
                    </details>
                  )
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Config */}
        {status && (
          <div className="p-6 bg-white dark:bg-gray-800 rounded-xl shadow-lg">
            <h2 className="text-xl font-semibold mb-4">Configuration</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <div className="text-sm text-muted-foreground">LLM Provider</div>
                <div className="font-medium">{status.config.llm_provider}</div>
              </div>
              <div className="space-y-1">
                <div className="text-sm text-muted-foreground">LLM Model</div>
                <div className="font-medium">{status.config.llm_model}</div>
              </div>
              <div className="space-y-1">
                <div className="text-sm text-muted-foreground">Memory</div>
                <div className="font-medium">{status.config.enable_memory ? 'Enabled' : 'Disabled'}</div>
              </div>
              <div className="space-y-1">
                <div className="text-sm text-muted-foreground">Plugins</div>
                <div className="font-medium">{status.config.enable_plugins ? 'Enabled' : 'Disabled'}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
