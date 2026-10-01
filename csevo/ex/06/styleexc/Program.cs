// 슬라이드 p6-v5-style-exc — 예외는 어디로 오나, C# 5.0
using System;
using System.IO;
using System.Threading.Tasks;

class App
{
    static Task<int> ReadClosed()
    {
        Stream s = new MemoryStream(new byte[4]);
        s.Dispose();                    // reading a closed stream fails
        return s.ReadAsync(new byte[4], 0, 4);
    }

    // ContinueWith: the failure arrives as task state
    static Task<string> WithContinue()
    {
        return ReadClosed().ContinueWith(t => t.IsFaulted
            ? "faulted: " + t.Exception.InnerException.GetType().Name
            : "read " + t.Result);
    }

    // await: catch it like synchronous code
    static async Task<string> WithAwait()
    {
        try { return "read " + await ReadClosed(); }
        catch (ObjectDisposedException e)
        {
            return "caught: " + e.GetType().Name;
        }
    }

    static void Main()
    {
        Console.WriteLine(WithContinue().Result);
        Console.WriteLine(WithAwait().Result);
    }
}
