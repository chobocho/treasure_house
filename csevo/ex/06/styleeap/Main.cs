// 슬라이드 p6-v5-style-eap — XxxAsync + XxxCompleted(EAP), C# 5.0
using System;
using System.IO;
using System.Text;
using System.Threading;

class App
{
    static void Main()
    {
        byte[] data = Encoding.ASCII.GetBytes("hello, async world");
        ChunkReader r = new ChunkReader(new MemoryStream(data));
        byte[] buf = new byte[8];
        int total = 0;
        ManualResetEvent done = new ManualResetEvent(false);
        r.ReadCompleted += (sender, e) =>
        {
            if (e.Count == 0) { done.Set(); return; }
            Console.WriteLine("read " + e.Count);
            total += e.Count;
            r.ReadAsync(buf);           // next read from the handler
        };
        r.ReadAsync(buf);
        done.WaitOne();
        Console.WriteLine("total " + total);
    }
}
