// 슬라이드 p5-v4-dyn-overload — 실행 중 오버로드 해석, C# 4.0
using System;

class Shape { }
class Circle : Shape { }
class Square : Shape { }

class Program
{
    static string Hit(Shape a, Shape b) { return "Shape-Shape"; }
    static string Hit(Circle a, Circle b) { return "Circle-Circle"; }
    static string Hit(Circle a, Square b) { return "Circle-Square"; }
    static string Hit(Square a, Shape b) { return "Square-Shape"; }

    static void Main()
    {
        Shape[] all = { new Circle(), new Square() };
        foreach (Shape a in all)
        {
            foreach (Shape b in all)
            {
                Console.WriteLine("{0,-6} {1,-6} {2,-11} {3}",
                    a.GetType().Name, b.GetType().Name,
                    Hit(a, b), Hit((dynamic)a, (dynamic)b));
            }
        }
    }
}
