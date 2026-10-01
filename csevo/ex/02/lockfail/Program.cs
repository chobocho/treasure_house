// 슬라이드 p2-v1-lock — 값 형식으로는 잠글 수 없다, C# 1.0
class App
{
    static int counter;

    static void Main()
    {
        lock (counter)                   // would lock a fresh box
        {
            counter++;
        }
    }
}
