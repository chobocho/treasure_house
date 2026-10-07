// 슬라이드 p15-v14-pe-sig — 두 조각의 서명 맞추기, C# 14
using System;

partial class Conn
{
    public partial Conn(string host, int port = 80);
#if ACCESS
    internal partial event Action Lost;
#else
    public partial event Action Lost;
#endif
}

partial class Conn
{
#if NAMES
    public partial Conn(string server, int port) =>
#elif DEFAULT
    public partial Conn(string host, int port = 8080) =>
#else
    public partial Conn(string host, int port) =>
#endif
        Console.WriteLine("port " + port);

    public partial event Action Lost { add { } remove { } }
}

class Program
{
    static void Main()
    {
        new Conn("a");
        new Conn(port: 1, host: "b");    // names of the defining part
    }
}
