// 슬라이드 p5-v4-dyn-where — dynamic 을 쓸 수 없는 자리, C# 4.0
using System;

class Program
{
    static void Main()
    {
        Type t = typeof(dynamic);
        object o = new dynamic();
        bool b = dynamic.Equals(1, 2);
    }
}
