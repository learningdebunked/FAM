import { useState } from 'react';
import Head from 'next/head';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';

export default function ComponentsTest() {
  const [checked, setChecked] = useState(false);
  const [emailNotifications, setEmailNotifications] = useState(false);
  const [pushNotifications, setPushNotifications] = useState(false);
  
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <Head>
        <title>UI Components Test</title>
      </Head>
      
      <div className="max-w-4xl mx-auto space-y-8">
        <h1 className="text-3xl font-bold mb-8">UI Components Test Page</h1>
        
        {/* Card Component Test */}
        <section>
          <h2 className="text-2xl font-semibold mb-4">Card Component</h2>
          <Card className="w-[350px]">
            <CardHeader>
              <CardTitle>Product Information</CardTitle>
              <CardDescription>View details about the selected product</CardDescription>
            </CardHeader>
            <CardContent>
              <p>This is a test card component with sample content to demonstrate its appearance and functionality.</p>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline">Cancel</Button>
              <Button>Continue</Button>
            </CardFooter>
          </Card>
        </section>

        {/* Button Component Test */}
        <section>
          <h2 className="text-2xl font-semibold mb-4">Button Variants</h2>
          <div className="flex flex-wrap gap-4">
            <Button>Default</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="link">Link</Button>
          </div>
          <div className="flex flex-wrap gap-4 mt-4">
            <Button size="sm">Small</Button>
            <Button>Default</Button>
            <Button size="lg">Large</Button>
            <Button size="icon">🔍</Button>
          </div>
        </section>

        {/* Switch Component Test */}
        <section>
          <h2 className="text-2xl font-semibold mb-4">Switch Component</h2>
          <div className="flex items-center space-x-2">
            <Switch 
              id="test-switch" 
              checked={checked} 
              onCheckedChange={setChecked}
            />
            <Label htmlFor="test-switch">
              {checked ? 'Enabled' : 'Disabled'}
            </Label>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Current state: {checked ? 'ON' : 'OFF'}
          </p>
        </section>

        {/* Combined Test */}
        <section>
          <h2 className="text-2xl font-semibold mb-4">Combined Example</h2>
          <Card>
            <CardHeader>
              <CardTitle>Notification Settings</CardTitle>
              <CardDescription>Configure your notification preferences</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="email-notifications">Email Notifications</Label>
                  <p className="text-sm text-gray-600">Receive email notifications</p>
                </div>
                <Switch 
                  id="email-notifications" 
                  checked={emailNotifications} 
                  onCheckedChange={setEmailNotifications}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="push-notifications">Push Notifications</Label>
                  <p className="text-sm text-gray-600">Receive push notifications</p>
                </div>
                <Switch 
                  id="push-notifications" 
                  checked={pushNotifications} 
                  onCheckedChange={setPushNotifications}
                />
              </div>
            </CardContent>
            <CardFooter className="flex justify-end gap-2">
              <Button variant="outline">Cancel</Button>
              <Button>Save Changes</Button>
            </CardFooter>
          </Card>
        </section>
      </div>
    </div>
  );
}
