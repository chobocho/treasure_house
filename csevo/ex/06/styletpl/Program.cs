// 슬라이드 p6-v5-style-tpl — Task 와 ContinueWith(C# 4 시절), C# 5.0
using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;

class App
{
    static Stream s;
    static byte[] buf = new byte[8];

    // Wrap the APM pair in a Task (TaskFactory.FromAsync)
    static Task<int> ReadChunk()
    {
        return Task<int>.Factory.FromAsync(
            s.BeginRead, s.EndRead, buf, 0, buf.Length, null);
    }

    // Loop by recursion: chain the next read
    static Task<int> Loop(int total)
    {
        return ReadChunk().ContinueWith(t =>
        {
            int n = t.Result;
            if (n == 0) return Task.FromResult(total);
            Console.WriteLine("read " + n);
            return Loop(total + n);
        }).Unwrap();
    }

    static void Main()
    {
        byte[] data = Encoding.ASCII.GetBytes("hello, async world");
        s = new MemoryStream(data);
        Console.WriteLine("total " + Loop(0).Result);
    }
}
