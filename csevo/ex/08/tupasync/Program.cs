// 슬라이드 p8-v7-tuple-async — async 메서드의 결과 둘, C# 7.0
using System;
using System.Threading.Tasks;

class App
{
    // out parameters are not allowed in async methods
    static async Task<(int count, long bytes)> ScanAsync()
    {
        await Task.Yield();
        return (3, 4096);
    }

#if BAD
    static async Task Scan2Async(out int count)
    {
        await Task.Yield();
        count = 3;
    }
#endif

    static void Main()
    {
        var r = ScanAsync().Result;
        Console.WriteLine(r.count + " files, " + r.bytes + " bytes");
    }
}
