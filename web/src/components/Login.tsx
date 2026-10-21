"use client";

import { useState } from "react";
import { login, setToken, type User } from "@/lib/api";
import Icon from "./Icon";
import SchoolMark from "./SchoolMark";
import styles from "./Login.module.css";

const DEMOS = [
  { type: "学生用户", user: "student", pass: "student123", desc: "查制度、问流程、看文件依据", icon: "chat" as const },
  { type: "部门管理员", user: "jwc_admin", pass: "admin123", desc: "维护部门文件，审核问答结果", icon: "building" as const },
  { type: "超级管理员", user: "admin", pass: "admin123", desc: "管理校园知识与系统运行", icon: "shield" as const },
];

export default function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (busy) return;
    setError(""); setBusy(true);
    try {
      const res = await login(username.trim(), password);
      setToken(res.token); onLogin(res.user);
    } catch (err) { setError(String(err instanceof Error ? err.message : err)); }
    finally { setBusy(false); }
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.ambientOne} /><div className={styles.ambientTwo} />
      <section className={styles.story}>
        <div className={styles.wordmark}><img src="/hdu/wordmark-white.svg" width={270} height={60} alt="杭州电子科技大学" /></div>
        <div className={styles.eyebrow}><span /> HANGZHOU DIANZI UNIVERSITY</div>
        <h1>校园里的疑问，<br />在这里找到依据。</h1>
        <p className={styles.lead}>从证明书补办到研究生办事，从图书馆资源到学期安排。让校园信息更好找，让每一个回答有出处。</p>
        <div className={styles.arch}>
          {[
            ["file", "查制度", "查阅本校公开文件"],
            ["building", "问流程", "了解材料与办理步骤"],
            ["shield", "看依据", "关键结论追溯原文"],
          ].map(([icon, title, text]) => <div key={title} className={styles.archItem}>
            <span className={styles.archIcon}><Icon name={icon as "database"} size={19} /></span>
            <div><b>{title}</b><small>{text}</small></div>
          </div>)}
        </div>
        <div className={styles.trust}><span /> 笃学力行 · 守正求新</div>
      </section>

      <section className={styles.loginSide}>
        <form className={styles.card} onSubmit={submit}>
          <div className={styles.mobileBrand}><SchoolMark /><span>杭电校园助手<small>杭州电子科技大学</small></span></div>
          <div className={styles.cardHead}>
            <span className={styles.kicker}>HDU CAMPUS ASSISTANT</span>
            <h2>欢迎使用杭电校园助手</h2>
            <p>登录后，开始查询校园制度与办事指南</p>
          </div>
          <label className={styles.field}><span>账号</span><div className={styles.inputWrap}><Icon name="agent" size={17}/><input value={username} onChange={e => setUsername(e.target.value)} placeholder="请输入账号" autoComplete="username" autoFocus /></div></label>
          <label className={styles.field}><span>密码</span><div className={styles.inputWrap}><Icon name="shield" size={17}/><input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="请输入密码" autoComplete="current-password" /></div></label>
          {error && <div className={styles.error}>{error}</div>}
          <button className={styles.submit} type="submit" disabled={busy}>{busy ? <><span className={styles.spinner}/>正在验证</> : <>安全登录 <Icon name="arrow" size={17}/></>}</button>
          <div className={styles.divider}><span>演示身份快速进入</span></div>
          <div className={styles.demoList}>{DEMOS.map(d => <button key={d.user} type="button" className={styles.demo} onClick={() => { setUsername(d.user); setPassword(d.pass); setError(""); }}>
            <span className={styles.demoIcon}><Icon name={d.icon} size={17}/></span><span><b>{d.type}</b><small>{d.desc}</small></span><code>{d.user}</code>
          </button>)}</div>
          <div className={styles.security}><Icon name="shield" size={14}/> 校园问答演示 · 依据账号角色进入对应工作台</div>
        </form>
      </section>
    </div>
  );
}
