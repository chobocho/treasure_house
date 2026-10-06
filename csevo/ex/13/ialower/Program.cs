// 슬라이드 p13-v12-ia-lower — 컴파일러가 만든 도우미, C# 12.0
using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

[InlineArray(4)] struct Buf { int _e; }

class App
{
    static void Main()
    {
        var b = new Buf();
        b[0] = 2;                          // element 0
        b[1] = 5;                          // element access
        Span<int> s = b;                   // conversion
        ReadOnlySpan<int> r = b;
        foreach (int v in b) { }           // foreach
        Console.WriteLine(s[1] + r[1]);

        var pid = typeof(App).Assembly.GetTypes()
            .Single(t => t.Name == "<PrivateImplementationDetails>");
        var ms = pid.GetMethods(BindingFlags.Static
                                | BindingFlags.NonPublic)
                    .Select(m => m.ToString())
                    .OrderBy(x => x, StringComparer.Ordinal);
        foreach (var m in ms) Console.WriteLine(m);
    }
}
