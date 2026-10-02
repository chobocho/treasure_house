// 슬라이드 p9-v8-runtime — C# 8.0 이 기대는 런타임과 라이브러리, C# 8.0
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;

class App
{
    static void Show(Type t, string usedBy)
    {
        Console.WriteLine("{0,-22} {1,-24} {2}", t.Name.Split('`')[0],
            t.Assembly.GetName().Name, usedBy);
    }

    static void Main()
    {
        Show(typeof(Index), "a[^1]");
        Show(typeof(Range), "a[1..3]");
        Show(typeof(IAsyncEnumerable<>), "await foreach");
        Show(typeof(IAsyncDisposable), "await using");
        Show(typeof(NotNullWhenAttribute), "nullable analysis");
        Console.WriteLine("DefaultImplementationsOfInterfaces: {0}",
            RuntimeFeature.IsSupported(
                RuntimeFeature.DefaultImplementationsOfInterfaces));
        Console.WriteLine("runtime {0}", Environment.Version);
    }
}
