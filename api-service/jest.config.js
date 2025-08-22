module.exports = {
  preset: "ts-jest",
  testEnvironment: "node",
  transform: { "^.+\\.(ts|tsx)$": "ts-jest" },
  moduleFileExtensions: ["ts", "tsx", "js", "jsx", "json", "node"],
  testMatch: ["**/tests/**/*.spec.(ts|js)"],

  // <-- add this block:
  moduleNameMapper: {
    "^src/(.*)$": "<rootDir>/$1",
  },
};
