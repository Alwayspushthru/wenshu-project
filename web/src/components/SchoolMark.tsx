export default function SchoolMark({ className, inverse = false }: { className?: string; inverse?: boolean }) {
  return <img className={className} src={`/hdu/crest-${inverse ? "white" : "blue"}.svg`} width={44} height={44} alt="杭州电子科技大学校徽" />;
}
