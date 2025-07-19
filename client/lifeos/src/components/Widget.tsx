export default function Widget() {

    const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    const date = new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric' });

    return (
        <div className="flex flex-col items-center justify-center glass-effect max-w-[301px] mx-auto py-8">
            <div className="text-center space-y-2">
                <div className="text-3xl font-mono text-text-primary">{time}</div>
                <div className="text-xl text-text-secondary">{date}</div>
            </div>
        </div>
    )
}