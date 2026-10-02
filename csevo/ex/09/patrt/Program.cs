// 슬라이드 p9-v8-pat-runtime — 패턴이 기대는 런타임 형식, C# 8.0
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

class App
{
    static void Show(Type t)
    {
        Console.WriteLine("{0}  [{1}]", t.FullName,
            t.Assembly.GetName().Name);
    }

    static void Main()
    {
        Show(typeof(SwitchExpressionException));
        Show(typeof(ITuple));
        // which tuple-like types answer ITuple at run time?
        object[] xs =
        {
            Tuple.Create(1, 2), (1, 2),
            new KeyValuePair<int, int>(1, 2), new[] { 1, 2 },
        };
        foreach (object o in xs)
            Console.WriteLine("{0,-22} ITuple: {1}", o.GetType().Name,
                o is ITuple t ? "yes, Length " + t.Length : "no");
    }
}
