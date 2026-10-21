uniform float uTime;
varying vec2 vUv;
varying vec3 vTint;
void main() {
  float distanceFromCenter = length(vUv - vec2(0.5));
  if (distanceFromCenter > 0.5) discard;
  float pulse = 0.85 + 0.15 * sin(uTime * 6.2831853 + vUv.y * 3.0);
  gl_FragColor = vec4(vTint * pulse, 1.0);
  // 선형 색을 렌더러의 출력 색 공간으로 변환한다.
  #include <colorspace_fragment>
}
