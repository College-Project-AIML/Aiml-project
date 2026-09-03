export default function SuvidhaMark({ size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" aria-hidden="true">
      <rect x="2" y="2" width="60" height="60" rx="14" fill="#17233D" fillOpacity="0.5" stroke="#E8823C" strokeOpacity="0.45" strokeWidth="1.2" />

      {/* Orange leaves: a growth canopy around the person. */}
      <g fill="#E8823C">
        <path d="M31 9c-6 5-6 12 0 16 6-4 6-11 0-16Z" />
        <path d="M21 12c-2 7 2 12 9 12 1-7-3-11-9-12Z" fillOpacity=".9" />
        <path d="M41 12c2 7-2 12-9 12-1-7 3-11 9-12Z" fillOpacity=".9" />
        <path d="M13 20c1 7 7 10 13 7-3-6-8-8-13-7Z" fillOpacity=".82" />
        <path d="M49 20c-1 7-7 10-13 7 3-6 8-8 13-7Z" fillOpacity=".82" />
        <path d="M10 31c4 6 11 6 15 1-5-5-11-5-15-1Z" fillOpacity=".72" />
        <path d="M52 31c-4 6-11 6-15 1 5-5 11-5 15-1Z" fillOpacity=".72" />
      </g>

      {/* Blue person: head, open arms, and body. */}
      <g fill="#F5F7FB">
        <circle cx="31" cy="30" r="5" />
        <path d="M28 36c-4 2-8 3-13 1l-1.5 2.8c5.4 3 10.6 2.4 15.1.4l-1 12h7l-1-12c4.5 2 9.7 2.6 15.1-.4L47 37c-5 2-9 1-13-1-1.3-1.2-4.7-1.2-6 0Z" />
      </g>
      <path d="M14 54c10-3 25-3 36 0" stroke="#E8823C" strokeOpacity=".85" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  )
}
