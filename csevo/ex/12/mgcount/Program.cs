// 슬라이드 p12-v11-mgcache-trap — 대리자의 정체에 기댄 코드, C# 11.0
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

class App
{
    static void Tick() { }

    // per-delegate state, keyed by object identity
    static readonly ConditionalWeakTable<Action, string> Tags = new();

    static void Register(Action a, string tag)
    {
        if (Tags.TryGetValue(a, out string old))
            Console.WriteLine($"{tag}: already tagged {old}");
        else
            Tags.Add(a, tag);
    }

    static void Main()
    {
        var seen = new HashSet<object>(
            ReferenceEqualityComparer.Instance);
        for (int i = 0; i < 1000; i++)
            seen.Add((Action)Tick);
        Console.WriteLine("distinct delegates: " + seen.Count);

        Register(Tick, "first");
        Register(Tick, "second");
        Action all = Tick;
        all += Tick;
        all -= Tick;
        int n = all.GetInvocationList().Length;
        Console.WriteLine("invocation list: " + n);
    }
}
