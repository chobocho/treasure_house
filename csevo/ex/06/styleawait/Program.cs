// 슬라이드 p6-v5-style-await — async/await 판, C# 5.0
using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;

class App
{
    // Same shape as the sync version: Read became await ReadAsync
    static async Task<int> CountAsync(Stream s)
    {
        byte[] buf = new byte[8];
        int total = 0, n;
        while ((n = await s.ReadAsync(buf, 0, buf.Length)) > 0)
        {
            Console.WriteLine("read " + n);
            total += n;
        }
        return total;
    }

    static void Main()
    {
        byte[] data = Encoding.ASCII.GetBytes("hello, async world");
        Stream s = new MemoryStream(data);
        Console.WriteLine("total " + CountAsync(s).Result);
    }
}
