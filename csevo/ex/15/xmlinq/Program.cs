// 슬라이드 p15-v14-xm-linq — 쿼리 식과 새 꼴의 확장 메서드, C# 14
using System;

class Box<T> { public T Value; public Box(T v) { Value = v; } }

static class BoxQuery
{
    extension<T>(Box<T> box)
    {
        public Box<R> Select<R>(Func<T, R> f) => new(f(box.Value));
        public Box<T> Where(Func<T, bool> p) =>
            p(box.Value) ? box : new Box<T>(default);
    }
}

class Program
{
    static void Main()
    {
        var b = new Box<int>(20);
        Box<string> q = from x in b
                        where x > 10
                        select "value " + (x + 1);
        Console.WriteLine(q.Value);
    }
}
