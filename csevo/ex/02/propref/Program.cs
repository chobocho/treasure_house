// 슬라이드 p2-v1-propref — 속성은 변수가 아니다, C# 1.0
struct Point { public int X; }

class Shape
{
    Point origin;
    public Point Origin
    {
        get { return origin; }
        set { origin = value; }
    }
    public int Width { get { return 0; } set { } }
}

class App
{
    static void Bump(ref int n) { n++; }

    static void Main()
    {
        Shape s = new Shape();
        Bump(ref s.Width);              // a property is not a variable
        s.Origin.X = 5;                 // would change a copy
    }
}
