// 슬라이드 p8-v7-tuple-iface — 인터페이스 구현과 원소 이름, C# 7.0
interface ISize
{
    (int width, int height) Size();
}

class Box : ISize
{
    public (int w, int h) Size() => (1, 2);     // other names
}

class App
{
    static void Main() { }
}
