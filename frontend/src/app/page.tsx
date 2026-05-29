import ChatUI from "@/components/ChatUI";

export const metadata = {
  title: "Sloth AI — AI Knowledge Chat",
  description: "Dual AI chat powered by YouTube channel knowledge bases.",
};

export default function Home() {
  return (
    <main className="min-h-screen p-4 md:p-6 flex flex-col items-center justify-center relative overflow-hidden">
      {/* Static deep background */}
      <div className="fixed inset-0 bg-[#07080d] -z-10" />

      <div className="z-10 w-full h-[92vh] flex max-w-4xl">
        <ChatUI />
      </div>
    </main>
  );
}
