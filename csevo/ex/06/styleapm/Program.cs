// 슬라이드 p6-v5-style-apm — Begin/End 짝(APM), C# 5.0
using System;
using System.IO;
using System.Text;
using System.Threading;

class App
{
    static Stream s;
    static byte[] buf = new byte[8];
    static int total;
    static ManualResetEvent done = new ManualResetEvent(false);

    static void Main()
    {
        byte[] data = Encoding.ASCII.GetBytes("hello, async world");
        s = new MemoryStream(data);
        s.BeginRead(buf, 0, buf.Length, OnRead, null);
        done.WaitOne();                 // wait for the end
        Console.WriteLine("total " + total);
    }

    // no loop: the callback starts the next read
    static void OnRead(IAsyncResult ar)
    {
        int n = s.EndRead(ar);
        if (n == 0) { done.Set(); return; }
        Console.WriteLine("read " + n);
        total += n;
        s.BeginRead(buf, 0, buf.Length, OnRead, null);
    }
}
