// 슬라이드 p2-v1-boxing — 박싱은 값을 복사한 새 객체, C# 1.0
using System;

class App
{
    static void Main()
    {
        int i = 1;
        object o = i;            // boxing: a copy on the heap
        i = 2;
        Console.WriteLine("i=" + i + " o=" + o);
        Console.WriteLine(o.GetType().FullName);

        int back = (int)o;       // unboxing: copy back out
        Console.WriteLine("back=" + back);

        object p = i, q = i;     // two boxings, two objects
        Console.WriteLine("same object? " + ReferenceEquals(p, q));
        Console.WriteLine("Equals?      " + p.Equals(q));
        Console.WriteLine("== ?         " + (p == q));
    }
}
