// 슬라이드 p2-v1-defctor — 기본 생성자가 사라질 때, C# 1.0
class Point
{
    int x, y;
    public Point(int x, int y) { this.x = x; this.y = y; }
}

class Point3 : Point                // implicit base() call
{
    int z;
    public Point3(int z) { this.z = z; }
}

class App
{
    static void Main()
    {
        Point p = new Point();      // no parameterless constructor
    }
}
