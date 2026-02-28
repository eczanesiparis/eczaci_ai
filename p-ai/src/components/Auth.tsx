import React, { useState } from 'react';
import { Lock, User as UserIcon, Loader2 } from 'lucide-react';
import axios from 'axios';

interface AuthProps {
    onLoginSuccess: (isAdmin: boolean, username: string) => void;
}

export function Auth({ onLoginSuccess }: AuthProps) {
    const [isLoginView, setIsLoginView] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [rememberMe, setRememberMe] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!username.trim() || !password.trim()) return;

        setIsLoading(true);
        setErrorMsg('');

        try {
            const endpoint = isLoginView ? '/api/login' : '/api/register';
            const res = await axios.post(`https://eczaci-ai.onrender.com${endpoint}`, { username, password });

            // local API fallback for development?
            // Actually, Render endpoint might not have this code deployed yet.
            // For now, if local dev, we might point to localhost. Let's use relative or localhost in dev.

            if (res.data.success) {
                const isAdmin = res.data.is_admin;
                if (rememberMe) {
                    localStorage.setItem('eczaci_auth', JSON.stringify({ loggedIn: true, admin: isAdmin, user: username }));
                } else {
                    sessionStorage.setItem('eczaci_auth', JSON.stringify({ loggedIn: true, admin: isAdmin, user: username }));
                }
                onLoginSuccess(isAdmin, username);
            }
        } catch (error: any) {
            if (error.response && error.response.data && error.response.data.detail) {
                setErrorMsg(error.response.data.detail);
            } else {
                setErrorMsg('Sunucu hatası oluştu, lütfen tekrar deneyin.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-full min-h-screen bg-slate-900 flex items-center justify-center p-4">
            <div className="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="p-8">
                    <div className="text-center mb-8">
                        <h2 className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-500 bg-clip-text text-transparent flex items-center justify-center gap-2">
                            <img src="/icon4.ico" alt="Eczacı AI" className="w-8 h-8 object-contain" />
                            Eczacı AI
                        </h2>
                        <p className="text-slate-500 mt-2 text-sm">
                            {isLoginView ? 'Devam etmek için giriş yapınız' : 'Yeni hesap oluşturunuz'}
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700">Kullanıcı Adı</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                                    <UserIcon size={18} />
                                </div>
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500 transition-all placeholder:text-slate-400 text-slate-900"
                                    placeholder="Kullanıcı adınız"
                                    required
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700">Şifre</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                                    <Lock size={18} />
                                </div>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500 transition-all placeholder:text-slate-400 text-slate-900"
                                    placeholder="Şifreniz"
                                    required
                                    minLength={6}
                                />
                            </div>
                        </div>

                        {errorMsg && (
                            <div className="p-3 bg-red-50 text-red-600 rounded-xl text-sm border border-red-100">
                                {errorMsg}
                            </div>
                        )}

                        {isLoginView && (
                            <div className="flex items-center">
                                <input
                                    id="remember-me"
                                    type="checkbox"
                                    checked={rememberMe}
                                    onChange={(e) => setRememberMe(e.target.checked)}
                                    className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded cursor-pointer"
                                />
                                <label htmlFor="remember-me" className="ml-2 block text-sm text-slate-600 cursor-pointer select-none">
                                    Beni Hatırla (Otomatik Giriş)
                                </label>
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full flex items-center justify-center bg-[#1E9E3D] hover:bg-[#198533] disabled:opacity-70 disabled:cursor-not-allowed text-white py-3.5 rounded-xl font-medium transition-colors mt-2"
                        >
                            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : (isLoginView ? 'Giriş Yap' : 'Kayıt Ol')}
                        </button>
                    </form>

                    <div className="mt-6 text-center text-sm text-slate-500">
                        {isLoginView ? (
                            <p>
                                Hesabınız yok mu?{' '}
                                <button onClick={() => { setIsLoginView(false); setErrorMsg(''); }} className="text-green-600 font-semibold hover:underline">
                                    Kayıt Olun
                                </button>
                            </p>
                        ) : (
                            <p>
                                Zaten hesabınız var mı?{' '}
                                <button onClick={() => { setIsLoginView(true); setErrorMsg(''); }} className="text-green-600 font-semibold hover:underline">
                                    Giriş Yapın
                                </button>
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
