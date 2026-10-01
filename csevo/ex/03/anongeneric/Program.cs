// 슬라이드 p3-v2-anon-generic — 제네릭 메서드 안의 익명 메서드, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static Predicate<T> EqualTo<T>(T target)
    {
        return delegate(T x)
        {
            return EqualityComparer<T>.Default.Equals(x, target);
        };
    }

    static void Show(Delegate d)
    {
        Type t = d.Target.GetType();
        Console.WriteLine("generic class " + t.IsGenericType
            + ", argument " + t.GetGenericArguments()[0].Name);
    }

    static void Main()
    {
        Predicate<int> is3 = EqualTo(3);
        Predicate<string> isA = EqualTo("a");
        Console.WriteLine(is3(3) + " " + isA("b"));
        Show(is3);
        Show(isA);
    }
}
