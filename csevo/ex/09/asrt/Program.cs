// 슬라이드 p9-v8-async-runtime — 5장이 기대는 런타임 형식, C# 8.0
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

class App
{
    static void Main()
    {
        Type[] types =
        {
            typeof(IAsyncEnumerable<>), typeof(IAsyncEnumerator<>),
            typeof(IAsyncDisposable), typeof(ValueTask<>),
            typeof(EnumeratorCancellationAttribute),
            typeof(AsyncIteratorMethodBuilder),
            typeof(ConfiguredCancelableAsyncEnumerable<>),
            typeof(TaskAsyncEnumerableExtensions),
        };
        foreach (Type t in types)
            Console.WriteLine("{0,-38} {1}", t.Name,
                t.Assembly.GetName().Name);
    }
}
