import { useState } from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

export function ProfileForm() {
  const [formData, setFormData] = useState({
    firstName: 'Jane',
    lastName: 'Doe',
    email: 'jane@example.com',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // mock save
    console.log('Profile saved', formData);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-bg-raised border border-border-subtle rounded-lg p-6">
      <div className="border-b border-border-subtle pb-4 mb-5 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-primary">Personal Information</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-secondary mb-2" htmlFor="firstName">
            First Name
          </label>
          <Input
            id="firstName"
            name="firstName"
            value={formData.firstName}
            onChange={handleChange}
            placeholder="Jane"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-secondary mb-2" htmlFor="lastName">
            Last Name
          </label>
          <Input
            id="lastName"
            name="lastName"
            value={formData.lastName}
            onChange={handleChange}
            placeholder="Doe"
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-secondary mb-2" htmlFor="email">
            Email Address
          </label>
          <Input
            id="email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="jane@example.com"
          />
        </div>
      </div>

      <div className="mt-6 flex justify-end">
        <Button intent="primary" size="sm" type="submit">
          Save Changes
        </Button>
      </div>
    </form>
  );
}
