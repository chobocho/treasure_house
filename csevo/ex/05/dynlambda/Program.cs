// 슬라이드 p5-v4-dyn-lambda — dynamic 호출에 람다 넘기기, C# 4.0
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        dynamic list = new List<int>();
        list.Add(3);
        list.Add(1);
#if BAD
        list.ForEach(x => Console.WriteLine(x));
#endif
        list.ForEach((Action<int>)(x => Console.WriteLine(x)));
        Action<int> twice = delegate(int x) {
            Console.WriteLine(x * 2); };
        list.ForEach(twice);
    }
}
