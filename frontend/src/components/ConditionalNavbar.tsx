'use client';

import { usePathname } from 'next/navigation';
import Navbar from './Navbar';

export default function ConditionalNavbar() {
  const pathname = usePathname();
  
  // Navbar를 숨길 페이지들
  const hideNavbarPaths = ['/login', '/signup'];
  const shouldShowNavbar = !hideNavbarPaths.includes(pathname);

  return shouldShowNavbar ? <Navbar /> : null;
}