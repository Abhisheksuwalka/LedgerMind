import { useAppContext } from '../store/AppContext';

export function useTheme() {
  const { theme, setTheme } = useAppContext();
  
  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return { theme, setTheme, toggleTheme };
}
