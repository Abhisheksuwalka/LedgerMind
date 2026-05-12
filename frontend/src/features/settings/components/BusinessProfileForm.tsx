import { useState } from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

export function BusinessProfileForm() {
  const [formData, setFormData] = useState({
    companyName: 'Acme Corp',
    industry: 'Software',
    fiscalYearEnd: '12-31',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // mock save
    console.log('Business Profile saved', formData);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-bg-raised border border-border-subtle rounded-lg p-6">
      <div className="border-b border-border-subtle pb-4 mb-5 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-primary">Business Profile</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-secondary mb-2" htmlFor="companyName">
            Company Name
          </label>
          <Input
            id="companyName"
            name="companyName"
            value={formData.companyName}
            onChange={handleChange}
            placeholder="e.g. Acme Corp"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-secondary mb-2" htmlFor="industry">
            Industry
          </label>
          <Input
            id="industry"
            name="industry"
            value={formData.industry}
            onChange={handleChange}
            placeholder="e.g. Software"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-secondary mb-2" htmlFor="fiscalYearEnd">
            Fiscal Year End (MM-DD)
          </label>
          <Input
            id="fiscalYearEnd"
            name="fiscalYearEnd"
            value={formData.fiscalYearEnd}
            onChange={handleChange}
            placeholder="12-31"
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
