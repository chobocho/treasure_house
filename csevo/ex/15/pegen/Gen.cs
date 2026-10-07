// 슬라이드 p15-v14-pe-gen — 생성기가 쓸 조각(손으로 쓴 대역), C# 14
using System;
using System.Collections.Generic;

partial class Button
{
    readonly List<(WeakReference Target, Action<object, string> Call)>
        clicked = new();

    public partial event Action<string> Clicked
    {
        add
        {
            var m = value.Method;
            clicked.Add((new WeakReference(value.Target),
                (t, s) => m.Invoke(t, new object[] { s })));
        }
        remove { }
    }

    void RaiseClicked(string s)
    {
        int alive = 0;
        foreach (var (target, call) in clicked)
            if (target.Target is object t) { alive++; call(t, s); }
        Console.WriteLine("  alive " + alive + "/" + clicked.Count);
    }
}
