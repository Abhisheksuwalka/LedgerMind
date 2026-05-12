import { useAppContext } from '../store/AppContext';

export function useUploadModal() {
  const { isUploadModalOpen, setIsUploadModalOpen } = useAppContext();
  
  const openModal = () => setIsUploadModalOpen(true);
  const closeModal = () => setIsUploadModalOpen(false);
  const toggleModal = () => setIsUploadModalOpen(!isUploadModalOpen);

  return { isUploadModalOpen, setIsUploadModalOpen, openModal, closeModal, toggleModal };
}
