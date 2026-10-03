// 슬라이드 p11-v10-runtime — C# 10 기능이 기대는 형식, C# 10.0
using System;
using System.Runtime.CompilerServices;
using System.Text;

record struct P(int X);

class App
{
    static void Show(Type t) =>
        Console.WriteLine(t.Name.PadRight(43)
            + t.Assembly.GetName().Name);

    static void Main()
    {
        foreach (Type i in typeof(P).GetInterfaces())
            Show(i);                                 // record struct
        Show(typeof(StringBuilder));                 // its ToString
        Show(typeof(IsExternalInit));                // init accessors
        Show(typeof(DefaultInterpolatedStringHandler));
        Show(typeof(InterpolatedStringHandlerAttribute));
        Show(typeof(
            InterpolatedStringHandlerArgumentAttribute));
        Show(typeof(CallerArgumentExpressionAttribute));
        Show(typeof(AsyncMethodBuilderAttribute));
        Show(typeof(PoolingAsyncValueTaskMethodBuilder));
    }
}
