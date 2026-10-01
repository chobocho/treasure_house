// 슬라이드 p6-v5-runtime — 같이 온 런타임, C# 5.0
using System;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

class App
{
    static void Show(Type t, string name)
    {
        int n = t.GetMethods().Count(m => m.Name == name);
        Console.WriteLine("{0,-36} {1,2}  {2}",
            t.Name + "." + name, n, t.Assembly.GetName().Name);
    }

    static void Main()
    {
        Show(typeof(Task), "Run");
        Show(typeof(Task), "Delay");
        Show(typeof(Task), "WhenAll");
        Show(typeof(Task), "WhenAny");
        Show(typeof(Task), "FromResult");
        Show(typeof(Task), "Yield");
        Show(typeof(Task), "ConfigureAwait");
        Show(typeof(Stream), "ReadAsync");
        Show(typeof(Stream), "CopyToAsync");
        Show(typeof(TextReader), "ReadToEndAsync");
        Show(typeof(CancellationTokenSource), "CancelAfter");
    }
}
