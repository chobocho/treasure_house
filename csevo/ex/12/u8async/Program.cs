// 슬라이드 p12-v11-utf8-async — async 메서드 안의 u8, C# 11.0
using System;
using System.IO;
using System.Threading.Tasks;

class App
{
    static async Task SendAsync(Stream s)
    {
        await s.WriteAsync("PING\r\n"u8.ToArray());     // copy: works
#if LOCAL
        ReadOnlySpan<byte> pong = "PONG\r\n"u8;     // ref struct local
        s.Write(pong);
#endif
#if CROSS
        ReadOnlySpan<byte> bye = "BYE\r\n"u8;
        await s.FlushAsync();                          // across await
        s.Write(bye);
#endif
        await s.FlushAsync();
    }

    static async Task Main()
    {
        var ms = new MemoryStream();
        await SendAsync(ms);
        Console.WriteLine(ms.Length + " bytes written");
    }
}
