// 슬라이드 p6-v5-style-sync — 동기 판(기준), C# 5.0
using System;
using System.IO;
using System.Text;

class App
{
    static void Main()
    {
        byte[] data = Encoding.ASCII.GetBytes("hello, async world");
        Stream s = new MemoryStream(data);
        byte[] buf = new byte[8];
        int total = 0, n;
        while ((n = s.Read(buf, 0, buf.Length)) > 0)
        {
            Console.WriteLine("read " + n);
            total += n;
        }
        Console.WriteLine("total " + total);
    }
}
