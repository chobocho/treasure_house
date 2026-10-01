// 슬라이드 p6-v5-tcswrap — 옛 꼴을 Task 로 감싸기, C# 5.0
using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;

class App
{
    // APM pair -> Task, by hand: the callback completes the task
    static Task<int> ReadTask(Stream s, byte[] buf)
    {
        TaskCompletionSource<int> tcs = new TaskCompletionSource<int>();
        s.BeginRead(buf, 0, buf.Length, ar =>
        {
            try { tcs.SetResult(s.EndRead(ar)); }
            catch (Exception e) { tcs.SetException(e); }
        }, null);
        return tcs.Task;
    }

    static async Task<int> CountAsync(Stream s)
    {
        byte[] buf = new byte[8];
        int total = 0, n;
        while ((n = await ReadTask(s, buf)) > 0)
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
