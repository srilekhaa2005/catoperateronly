import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Activity, ClipboardList, ShieldAlert, Wrench, FileWarning, GraduationCap, MessageSquareText, Menu, X, Bell, Languages } from 'lucide-react';

const nav=[['/','Dashboard',Activity],['/tasks','Daily Tasks',ClipboardList],['/safety','Safety Monitoring',ShieldAlert],['/machines','Machine Insights',Wrench],['/incident','Incident Logging',FileWarning],['/training','Training Hub',GraduationCap],['/assistant','Operator Assistant',MessageSquareText]];
export default function Layout({children,operator,language,setLanguage,alertCount}){
 const [open,setOpen]=useState(false);
 return <div className="min-h-screen bg-[#111214] text-zinc-100">
  <header className="sticky top-0 z-40 border-b border-white/10 bg-[#151618]/95 backdrop-blur"><div className="mx-auto flex h-16 max-w-[1500px] items-center justify-between px-4 lg:px-6">
   <div className="flex items-center gap-3"><button className="btn-secondary p-2 lg:hidden" onClick={()=>setOpen(!open)}>{open?<X size={18}/>:<Menu size={18}/>}</button><div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cat-yellow font-black text-black">CAT</div><div><div className="font-bold tracking-tight">Operator Copilot</div><div className="hidden text-[10px] uppercase tracking-[.2em] text-zinc-500 sm:block">Smart machine operations</div></div></div>
   <div className="flex items-center gap-2"><div className="hidden items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs sm:flex"><Languages size={15}/><select value={language} onChange={e=>setLanguage(e.target.value)} className="bg-transparent outline-none"><option className="bg-zinc-900" value="en">English</option><option className="bg-zinc-900" value="ta">தமிழ்</option><option className="bg-zinc-900" value="hi">हिन्दी</option></select></div><div className="relative rounded-xl border border-white/10 p-2"><Bell size={17}/>{alertCount>0&&<span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[9px] font-bold">{alertCount}</span>}</div><div className="hidden text-right sm:block"><div className="text-sm font-semibold">{operator.name}</div><div className="text-xs text-zinc-500">{operator.employee_code}</div></div><div className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-700 text-sm font-bold">{operator.name.split(' ').map(x=>x[0]).join('')}</div></div>
  </div></header>
  <div className="mx-auto flex max-w-[1500px]">
   <aside className={`${open?'block':'hidden'} fixed inset-y-16 left-0 z-30 w-64 border-r border-white/10 bg-[#151618] p-3 lg:sticky lg:top-16 lg:block lg:h-[calc(100vh-4rem)] lg:self-start`}>
    <nav className="space-y-1">{nav.map(([to,label,Icon])=><NavLink key={to} to={to} end={to==='/' } onClick={()=>setOpen(false)} className={({isActive})=>`flex items-center gap-3 rounded-xl px-3 py-3 text-sm ${isActive?'bg-cat-yellow font-bold text-black':'text-zinc-400 hover:bg-white/5 hover:text-white'}`}><Icon size={18}/>{label}</NavLink>)}</nav>
    <div className="mt-6 rounded-2xl border border-white/10 bg-white/[.03] p-4"><div className="mb-2 text-xs font-bold uppercase tracking-widest text-zinc-500">System</div><div className="flex items-center gap-2 text-xs text-emerald-400"><span className="h-2 w-2 rounded-full bg-emerald-400"/> Demo data connected</div><p className="mt-2 text-xs leading-5 text-zinc-500">API calls automatically fall back to realistic fixtures when the backend is unavailable.</p></div>
   </aside>
   <main className="min-w-0 flex-1 p-4 lg:p-6">{children}</main>
  </div>
 </div>
}
