// 슬라이드 p13-v12-ce-actions — 원소는 object 로 바뀌어야 한다, C# 12
using System;
using System.Collections;
using System.Collections.Generic;

class Actions : IEnumerable
{
    readonly List<Action<int>> list = [];
    public void Add(Action<int> action) { list.Add(action); }
    public IEnumerator GetEnumerator() => list.GetEnumerator();
}

class Program
{
    static void Main()
    {
        Actions a = [(int x) => Console.WriteLine("typed " + x),
            (Action<int>)(x => Console.WriteLine("cast " + x))];
        foreach (Action<int> f in a) f(1);
        var old = new Actions { x => Console.WriteLine("init " + x) };
        foreach (Action<int> f in old) f(2);
#if BAD
        Actions bad = [_ => { }];
#endif
    }
}
