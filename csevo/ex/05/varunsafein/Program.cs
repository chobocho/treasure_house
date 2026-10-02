// 슬라이드 p5-v4-var-safety-in — in T 를 내보내는 자리에 두면, C# 4.0
using System.Collections.Generic;

interface ISink<in T>
{
    void Put(T item);
    T Take();
    List<T> All { get; }
}

class Program
{
    static void Main()
    {
    }
}
